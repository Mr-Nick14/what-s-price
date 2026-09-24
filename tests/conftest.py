"""Общие фикстуры тестов."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from what_s_price.service.app import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def good_row() -> dict[str, object]:
    return json.loads(Path("good.json").read_text(encoding="utf-8"))
