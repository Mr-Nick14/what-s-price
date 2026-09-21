"""PostgreSQL persistence for prediction requests."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from what_s_price.config import settings

DDL = """
CREATE TABLE IF NOT EXISTS predictions (
    request_id UUID PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL DEFAULT now(),
    model_version TEXT NOT NULL,
    features JSONB NOT NULL,
    prediction DOUBLE PRECISION NOT NULL,
    latency_ms REAL NOT NULL,
    status_code SMALLINT NOT NULL
)
"""


def init() -> None:
    """Create the prediction table when PostgreSQL logging is configured."""

    if not settings.database_url:
        return

    with psycopg.connect(settings.database_url) as connection:
        connection.execute("SELECT pg_advisory_xact_lock(7001)")
        connection.execute(DDL)


def save_prediction(
    request_id: str,
    features: dict[str, Any],
    prediction: float,
    model_version: str,
    latency_ms: float,
    status_code: int,
) -> None:
    """Persist one completed prediction without affecting API-only deployments."""

    if not settings.database_url:
        return

    with psycopg.connect(settings.database_url) as connection:
        connection.execute(
            """
            INSERT INTO predictions (
                request_id, model_version, features, prediction, latency_ms, status_code
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                request_id,
                model_version,
                Jsonb(features),
                prediction,
                latency_ms,
                status_code,
            ),
        )
