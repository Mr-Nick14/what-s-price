"""Нагрузка на API."""

import json
from pathlib import Path

from locust import HttpUser, between, task

GOOD_ROW = json.loads(Path(__file__).with_name("good.json").read_text(encoding="utf-8"))


class PriceUser(HttpUser):
    wait_time = between(0.05, 0.2)

    @task(5)
    def predict(self) -> None:
        self.client.post("/v1/predict", json=GOOD_ROW, name="POST /v1/predict")

    @task(1)
    def health(self) -> None:
        self.client.get("/health", name="GET /health")
