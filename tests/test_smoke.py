"""Проверки успешного прогноза."""

from what_s_price import db


def test_predict_smoke(client, good_row) -> None:
    response = client.post("/v1/predict", json=good_row)
    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] > 0
    assert body["latency_ms"] >= 0
    assert body["model_version"] == "0.1.0"
    assert body["request_id"]


def test_predict_handles_missing_mileage(client, good_row) -> None:
    response = client.post("/v1/predict", json={**good_row, "mileage": None})
    assert response.status_code == 200


def test_same_car_gets_same_price(client, good_row) -> None:
    first = client.post("/v1/predict", json=good_row)
    second = client.post("/v1/predict", json=good_row)
    assert first.status_code == second.status_code == 200
    assert first.json()["prediction"] == second.json()["prediction"]


def test_prediction_is_logged(client, good_row, monkeypatch) -> None:
    logged_rows: list[tuple[object, ...]] = []
    monkeypatch.setattr(db, "save_prediction", lambda *args: logged_rows.append(args))

    response = client.post("/v1/predict", json=good_row)
    assert response.status_code == 200
    assert len(logged_rows) == 1
    assert logged_rows[0][0] == response.json()["request_id"]
    assert logged_rows[0][-1] == 200
