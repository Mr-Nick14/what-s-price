"""Runtime settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings shared by the API and prediction logger."""

    model_artifact_path: str = "artifacts/model.joblib"
    database_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
