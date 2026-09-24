"""Журнал прогнозов в PostgreSQL."""

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
    prediction DOUBLE PRECISION,
    latency_ms REAL NOT NULL,
    status_code SMALLINT NOT NULL
)
"""


def init() -> None:
    """Создать таблицу журнала."""
    if not settings.database_url:
        return

    with psycopg.connect(settings.database_url) as connection:
        # Две реплики могут запуститься одновременно.
        connection.execute("SELECT pg_advisory_xact_lock(7001)")
        connection.execute(DDL)
        # Ошибки 422 сохраняются без прогноза.
        connection.execute("ALTER TABLE predictions ALTER COLUMN prediction DROP NOT NULL")


def save_prediction(
    request_id: str,
    features: dict[str, Any],
    prediction: float | None,
    model_version: str,
    latency_ms: float,
    status_code: int,
) -> None:
    """Сохранить запрос."""
    if not settings.database_url:
        return

    with psycopg.connect(settings.database_url) as connection:
        connection.execute(
            """
            INSERT INTO predictions
                (request_id, model_version, features, prediction, latency_ms, status_code)
            VALUES (%s, %s, %s, %s, %s, %s)
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
