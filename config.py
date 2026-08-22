"""Centralized configuration. Reads from environment + .env file."""
from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini - primary model is set via env; we auto-fallback through a queue
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"

    # Fallback queue (tried in order if primary hits 429/503/quota).
    # gemini-3.5-flash and gemini-3.6-flash have a hard 20/day free-tier cap,
    # so we keep them last.  gemini-3.5-flash-lite has higher RPM and no
    # observed daily cap on the free tier.
    gemini_fallback_models: str = "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.5-flash,gemini-3.6-flash"

    # GCP
    google_cloud_project: str = ""
    google_cloud_region: str = "us-central1"
    firestore_collection: str = "exam_mitra"

    # Runtime
    environment: str = "local"  # "local" | "cloud"

    # Optional: SendGrid (for email reminders)
    sendgrid_api_key: str = ""
    from_email: str = "nope@exammitra.app"

    @property
    def is_cloud(self) -> bool:
        return self.environment == "cloud" or bool(
            os.environ.get("K_SERVICE")  # set automatically by Cloud Run
        )

    @property
    def model_fallback_list(self) -> list[str]:
        """Return [primary] + fallbacks, deduplicated and as a list."""
        models = [self.gemini_model]
        for m in self.gemini_fallback_models.split(","):
            m = m.strip()
            if m and m not in models:
                models.append(m)
        return models


settings = Settings()
# When running on Cloud Run, auto-detect project from metadata server if not set
if settings.is_cloud and not settings.google_cloud_project:
    try:
        import google.auth
        _, project_id = google.auth.default()
        settings.google_cloud_project = project_id or ""
    except Exception:
        pass

# Paths
ROOT_DIR = Path(__file__).parent
STATIC_DIR = ROOT_DIR / "static"
TEMPLATES_DIR = ROOT_DIR / "templates"
