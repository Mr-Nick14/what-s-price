"""Shared fixtures for API contract tests."""

import pytest
from fastapi.testclient import TestClient

from what_s_price.service.app import app


@pytest.fixture()
def client():
    """Start the application lifespan for each isolated API test."""

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def valid_car() -> dict[str, object]:
    """A valid request using actual artifact feature names and types."""

    return {
        "make_name": "Nissan",
        "model_name": "Sentra",
        "year": 2020,
        "mileage": 5.0,
        "engine_displacement": 2000.0,
        "horsepower": 149.0,
        "fuel_type": "Gasoline",
        "transmission_display": "Continuously Variable Transmission",
        "body_type": "Sedan",
        "wheel_system": "FWD",
        "is_new": True,
        "has_accidents": None,
    }
