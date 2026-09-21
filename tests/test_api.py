"""Contract tests for the prediction API."""

from fastapi.testclient import TestClient

from what_s_price import db


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_after_lifespan_loads_model(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_predict_returns_contract(client: TestClient, valid_car: dict[str, object]) -> None:
    response = client.post("/v1/predict", json=valid_car)

    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] > 0
    assert body["model_version"] == "0.1.0"
    assert body["request_id"]
    assert body["latency_ms"] >= 0


def test_invalid_input_returns_422(client: TestClient, valid_car: dict[str, object]) -> None:
    response = client.post("/v1/predict", json={**valid_car, "year": 1700})

    assert response.status_code == 422


def test_extra_field_returns_422(client: TestClient, valid_car: dict[str, object]) -> None:
    response = client.post("/v1/predict", json={**valid_car, "unexpected": "value"})

    assert response.status_code == 422


def test_missing_required_field_returns_422(
    client: TestClient,
    valid_car: dict[str, object],
) -> None:
    request_without_model = dict(valid_car)
    del request_without_model["model_name"]

    response = client.post("/v1/predict", json=request_without_model)

    assert response.status_code == 422


def test_prediction_is_deterministic(client: TestClient, valid_car: dict[str, object]) -> None:
    first = client.post("/v1/predict", json=valid_car)
    second = client.post("/v1/predict", json=valid_car)

    assert first.status_code == second.status_code == 200
    assert first.json()["prediction"] == second.json()["prediction"]


def test_prediction_log_has_success_status(
    client: TestClient,
    valid_car: dict[str, object],
    monkeypatch,
) -> None:
    logged_rows: list[tuple[object, ...]] = []
    monkeypatch.setattr(db, "save_prediction", lambda *args: logged_rows.append(args))

    response = client.post("/v1/predict", json=valid_car)

    assert response.status_code == 200
    assert len(logged_rows) == 1
    assert logged_rows[0][0] == response.json()["request_id"]
    assert logged_rows[0][-1] == 200
