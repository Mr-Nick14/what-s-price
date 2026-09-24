"""Проверка схемы артефакта."""

from pathlib import Path

from what_s_price.service.app import Features, load_model_bundle


def test_artifact_schema_matches_api_features() -> None:
    _, metadata = load_model_bundle(Path("artifacts/model.joblib"))

    assert metadata["target"] == "price"
    assert metadata["input_features"] == list(Features.model_fields)
    assert set(metadata["metrics_test"]) == {"mae", "rmse", "r2"}
