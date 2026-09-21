# What's Price

Учебный ML-сервис для оценки цены объявления подержанного автомобиля. Модель обучена
на исторических объявлениях: baseline — `DummyRegressor` с медианой, основной вариант —
`LinearRegression` в едином `scikit-learn` pipeline. Артефакт включает pipeline, метаданные,
версию модели и SHA-256 исходного датасета.

## Быстрый старт

```bash
uv sync --all-groups
uv run pytest -q
docker compose up --build
```

API доступно по адресу `http://127.0.0.1:8000`. Контракт и примеры запроса находятся в
`/docs`; служебные endpoints — `/health` и `/ready`; прогноз — `POST /v1/predict`.

Compose запускает API и PostgreSQL. Каждый успешный прогноз сохраняется в таблице
`predictions` вместе с UUID запроса, набором признаков, версией модели, прогнозом,
задержкой и HTTP-статусом. Kubernetes-манифесты лежат в [k8s](k8s): они описывают API,
PostgreSQL, сервисы, конфигурацию, секрет и probes.

## Структура

- `notebooks/01_baseline.ipynb` — воспроизводимое обучение и сравнение baseline.
- `artifacts/model.joblib` — версионированный bundle модели.
- `src/what_s_price/service/app.py` — FastAPI-приложение и контракт API.
- `src/what_s_price/db.py` — инициализация PostgreSQL и журналирование прогнозов.
- `tests/` — проверки API и артефакта.
- `docs/evidence/` и [REPORT.md](REPORT.md) — отчёт и скриншоты чекпоинтов.
