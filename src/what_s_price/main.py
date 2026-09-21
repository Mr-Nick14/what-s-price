"""FastAPI application for used-car price predictions."""

from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_ARTIFACT_PATH = Path("artifacts/model.joblib")


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


def artifact_path_from_environment() -> Path:
    """Resolve the artifact path without coupling loading to the current module path."""

    return Path(os.environ.get("MODEL_ARTIFACT_PATH", DEFAULT_ARTIFACT_PATH))


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
    """Load the model once when the application starts."""

    pipeline, metadata = load_model_bundle(artifact_path_from_environment())
    app.state.pipeline = pipeline
    app.state.metadata = metadata
    yield
    app.state.pipeline = None
    app.state.metadata = None


app = FastAPI(
    title="What\'s Price API",
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
def predict(features: CarFeatures, request: Request) -> PredictResponse:
    """Predict one price while preserving the artifact feature order."""

    started_at = time.perf_counter()
    metadata = request.app.state.metadata
    frame = pd.DataFrame(
        [features.model_dump()],
        columns=metadata["input_features"],
    )
    prediction = float(request.app.state.pipeline.predict(frame)[0])
    latency_ms = round((time.perf_counter() - started_at) * 1_000, 3)

    return PredictResponse(
        prediction=prediction,
        model_version=metadata["model_version"],
        request_id=str(uuid.uuid4()),
        latency_ms=latency_ms,
    )
