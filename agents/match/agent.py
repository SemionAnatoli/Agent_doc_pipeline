from __future__ import annotations

import json
from pathlib import Path

from core.config import JOBS_DIR
from core.schemas import ExtractionResult, ExtractionStatus, MatchStatus, MatchingResult
from tools.crm_registry import lookup_companies_by_inn
from tools.extraction_manifest import load_extraction_result


def run_match(extraction: ExtractionResult) -> MatchingResult:
    base = MatchingResult(job_id=extraction.job_id, status=MatchStatus.FAILED)

    if extraction.status != ExtractionStatus.OK:
        return base.model_copy(
            update={
                "status": MatchStatus.SKIPPED,
                "rejection_reason": "extract_not_ok",
                "notes": f"extract_status={extraction.status.value}",
            }
        )
    if extraction.entities is None:
        return base.model_copy(
            update={
                "status": MatchStatus.SKIPPED,
                "rejection_reason": "entities_missing",
            }
        )

    checked, matches = lookup_companies_by_inn(extraction.entities.inn_candidates)
    status = MatchStatus.OK if matches else MatchStatus.NO_MATCH
    result = MatchingResult(
        job_id=extraction.job_id,
        status=status,
        checked_inn=checked,
        matches=matches,
        notes="matched_by_inn_from_local_registry",
    )

    out = JOBS_DIR / extraction.job_id / "matching.json"
    out.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def run_match_by_job_id(job_id: str) -> MatchingResult | None:
    ext = load_extraction_result(job_id.strip())
    if ext is None:
        return None
    return run_match(ext)
