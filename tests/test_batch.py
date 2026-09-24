"""Проверки пакетного прогноза."""

from unittest.mock import Mock


def test_batch_matches_single_prediction(client, good_row) -> None:
    single = client.post("/v1/predict", json=good_row).json()["prediction"]
    batch = client.post("/v1/predict/batch", json={"rows": [good_row] * 3})

    assert batch.status_code == 200
    assert batch.json()["predictions"] == [single] * 3
    assert batch.json()["latency_ms"] >= 0
    assert batch.json()["model_version"] == "0.1.0"


def test_batch_invokes_pipeline_once(client, good_row, monkeypatch) -> None:
    pipeline = client.app.state.pipeline
    spy = Mock(wraps=pipeline.predict)
    monkeypatch.setattr(pipeline, "predict", spy)

    response = client.post("/v1/predict/batch", json={"rows": [good_row] * 500})

    assert response.status_code == 200
    assert len(response.json()["predictions"]) == 500
    spy.assert_called_once()
    assert len(spy.call_args.args[0]) == 500


def test_batch_rejects_empty_or_oversized_input(client, good_row) -> None:
    assert client.post("/v1/predict/batch", json={"rows": []}).status_code == 422
    assert client.post("/v1/predict/batch", json={"rows": [good_row] * 1001}).status_code == 422
