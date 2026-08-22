"""Database abstraction.

On Cloud Run: uses Google Cloud Firestore (required GCP service per rules).
Locally: uses a simple JSON file in ./data/ so developers don't need to
set up Firestore emulator to hack on the project.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
def _utcnow(): return datetime.now(timezone.utc)
from pathlib import Path
from typing import Optional

from config import settings, ROOT_DIR
from models.schemas import StudyPlanState

logger = logging.getLogger(__name__)

LOCAL_DB_PATH = ROOT_DIR / "data" / "jobs.json"
LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class JobStore:
    """Key-value store for StudyPlanState, persisted across restarts."""

    def __init__(self) -> None:
        self._memory: dict[str, StudyPlanState] = {}
        self._use_firestore = settings.is_cloud and settings.google_cloud_project
        if self._use_firestore:
            try:
                from google.cloud import firestore
                self._client = firestore.Client(project=settings.google_cloud_project)
                self._col = self._client.collection(settings.firestore_collection)
                logger.info("JobStore: using Firestore (%s)", settings.firestore_collection)
            except Exception as e:
                logger.warning("Firestore init failed, falling back to local JSON: %s", e)
                self._use_firestore = False
        if not self._use_firestore:
            self._load_local()

    # ---- local (dev) ----

    def _load_local(self) -> None:
        if not LOCAL_DB_PATH.exists():
            return
        try:
            raw = json.loads(LOCAL_DB_PATH.read_text())
            for job_id, data in raw.items():
                self._memory[job_id] = StudyPlanState.model_validate(data)
        except Exception as e:
            logger.warning("Failed to load local DB: %s", e)
            self._memory = {}

    def _save_local(self) -> None:
        raw = {jid: s.model_dump(mode="json") for jid, s in self._memory.items()}
        LOCAL_DB_PATH.write_text(json.dumps(raw, indent=2, default=str))

    # ---- public API ----

    def get(self, job_id: str) -> Optional[StudyPlanState]:
        if self._use_firestore:
            doc = self._col.document(job_id).get()
            if not doc.exists:
                return None
            return StudyPlanState.model_validate(doc.to_dict())
        return self._memory.get(job_id)

    def save(self, state: StudyPlanState) -> None:
        state.updated_at = datetime.utcnow()
        if self._use_firestore:
            self._col.document(state.job_id).set(state.model_dump(mode="json"))
        else:
            self._memory[state.job_id] = state
            self._save_local()

    def delete(self, job_id: str) -> None:
        if self._use_firestore:
            self._col.document(job_id).delete()
        else:
            self._memory.pop(job_id, None)
            self._save_local()


# Singleton
store = JobStore()
