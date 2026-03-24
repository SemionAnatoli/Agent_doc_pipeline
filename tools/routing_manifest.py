from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from core.config import JOBS_DIR
from core.schemas import RoutingResult


def routing_manifest_path(job_id: str) -> Path:
    return JOBS_DIR / job_id / "routing.json"


def load_routing_result(job_id: str) -> RoutingResult | None:
    path = routing_manifest_path(job_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    try:
        return RoutingResult.model_validate(data)
    except ValidationError:
        return None
