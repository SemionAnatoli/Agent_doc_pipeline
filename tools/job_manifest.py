import json
from pathlib import Path

from pydantic import ValidationError

from core.config import JOBS_DIR
from core.schemas import IngestionResult


def intake_manifest_path(job_id: str) -> Path:
    return JOBS_DIR / job_id / "intake.json"


def load_intake_result(job_id: str) -> IngestionResult | None:
    path = intake_manifest_path(job_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return IngestionResult.model_validate(data)
    except (json.JSONDecodeError, ValidationError, ValueError):
        return None
