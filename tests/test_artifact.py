"""Tests for the artifact contract used by the API."""

from pathlib import Path

from what_s_price.service.app import CarFeatures, load_model_bundle


def test_artifact_schema_matches_api_features() -> None:
    _, metadata = load_model_bundle(Path("artifacts/model.joblib"))

    assert metadata["target"] == "price"
    assert metadata["input_features"] == list(CarFeatures.model_fields)
    assert set(metadata["metrics_test"]) == {"mae", "rmse", "r2"}
