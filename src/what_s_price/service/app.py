"""FastAPI application for used-car price predictions."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import joblib
import pandas as pd
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from what_s_price import db
from what_s_price.config import settings


class CarFeatures(BaseModel):
    """Features accepted by the trained used-car-price model."""

    model_config = ConfigDict(extra="forbid", strict=True)

    make_name: str = Field(min_length=1, max_length=100)
    model_name: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1886, le=2021)
    mileage: float | None = Field(default=None, ge=0, le=1_000_000)
    engine_displacement: float | None = Field(default=None, ge=0, le=10_000)
    horsepower: float | None = Field(default=None, ge=0, le=2_000)
    fuel_type: str | None = Field(default=None, min_length=1, max_length=100)
    transmission_display: str | None = Field(default=None, min_length=1, max_length=100)
    body_type: str | None = Field(default=None, min_length=1, max_length=100)
    wheel_system: str | None = Field(default=None, min_length=1, max_length=100)
    is_new: bool
    has_accidents: bool | None = None


class HealthResponse(BaseModel):
    status: str


class PredictResponse(BaseModel):
    prediction: float
    model_version: str
    request_id: str
    latency_ms: float


def load_model_bundle(path: Path) -> tuple[Any, dict[str, Any]]:
    """Load and validate the joblib bundle created by the training notebook."""

    if not path.is_file():
        raise FileNotFoundError(f"Model artifact not found: {path}")

    bundle = joblib.load(path)
    if not isinstance(bundle, dict) or {"pipeline", "metadata"} - bundle.keys():
        raise ValueError("Model artifact must be a bundle with pipeline and metadata")

    metadata = bundle["metadata"]
    if not isinstance(metadata, dict) or not {
        "input_features",
        "model_version",
    } <= metadata.keys():
        raise ValueError("Model metadata is missing required fields")

    if list(metadata["input_features"]) != list(CarFeatures.model_fields):
        raise ValueError("API schema does not match the model artifact feature order")

    return bundle["pipeline"], metadata


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load the model and initialize optional PostgreSQL logging once at startup."""

    pipeline, metadata = load_model_bundle(Path(settings.model_artifact_path))
    app.state.pipeline = pipeline
    app.state.metadata = metadata
    db.init()
    yield
    app.state.pipeline = None
    app.state.metadata = None


app = FastAPI(
    title="What's Price API",
    version="1.0.0",
    description="Predicts the listing price of a used car.",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report that the process is alive."""

    return HealthResponse(status="ok")


@app.get("/ready", response_model=HealthResponse)
def ready(request: Request) -> HealthResponse:
    """Report readiness only after the model was loaded during startup."""

    if getattr(request.app.state, "pipeline", None) is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    return HealthResponse(status="ready")


@app.post("/v1/predict", response_model=PredictResponse)
def predict(
    features: CarFeatures,
    request: Request,
    background_tasks: BackgroundTasks,
) -> PredictResponse:
    """Predict one price and schedule persistence when PostgreSQL is configured."""

    started_at = time.perf_counter()
    metadata = request.app.state.metadata
    payload = features.model_dump()
    frame = pd.DataFrame([payload], columns=metadata["input_features"])
    prediction = float(request.app.state.pipeline.predict(frame)[0])
    latency_ms = round((time.perf_counter() - started_at) * 1_000, 3)
    request_id = str(uuid.uuid4())

    background_tasks.add_task(
        db.save_prediction,
        request_id,
        payload,
        prediction,
        metadata["model_version"],
        latency_ms,
        200,
    )

    return PredictResponse(
        prediction=prediction,
        model_version=metadata["model_version"],
        request_id=request_id,
        latency_ms=latency_ms,
    )
