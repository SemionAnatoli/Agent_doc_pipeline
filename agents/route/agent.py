from __future__ import annotations

import json

from core.config import JOBS_DIR
from core.schemas import ExtractionStatus, MatchStatus, RouteStatus, RoutingResult
from tools.extraction_manifest import load_extraction_result
from tools.matching_manifest import load_matching_result


def run_route_by_job_id(job_id: str) -> RoutingResult | None:
    job = job_id.strip()
    extraction = load_extraction_result(job)
    matching = load_matching_result(job)
    if extraction is None or matching is None:
        return None

    base = RoutingResult(job_id=job, status=RouteStatus.FAILED)

    if extraction.status != ExtractionStatus.OK:
        result = base.model_copy(
            update={
                "status": RouteStatus.REVIEW_REQUIRED,
                "queue": "ocr_review",
                "priority": "high",
                "reasons": ["Text extraction was skipped or failed — document may be a scanned image"],
                "next_actions": [
                    "Verify the input file quality",
                    "Enable OCR processing for scanned documents",
                ],
                "notes": "routing_from_extract_and_match",
            }
        )
    elif matching.status == MatchStatus.OK:
        reasons = ["Counterparty matched in CRM"]
        if len(matching.checked_inn) > 1:
            reasons.append("Multiple INN candidates were evaluated")
        result = base.model_copy(
            update={
                "status": RouteStatus.READY_FOR_TEMPLATE,
                "queue": "templating",
                "priority": "normal",
                "reasons": reasons,
                "next_actions": [
                    "Generate outgoing document template",
                    "Send prepared document to the recipient",
                ],
                "notes": "routing_from_extract_and_match",
            }
        )
    elif matching.status == MatchStatus.NO_MATCH:
        result = base.model_copy(
            update={
                "status": RouteStatus.REVIEW_REQUIRED,
                "queue": "crm_enrichment",
                "priority": "high",
                "reasons": ["INN was not matched to any company in the CRM database"],
                "next_actions": [
                    "Verify the extracted INN manually",
                    "Add or update the counterparty record in CRM",
                ],
                "notes": "routing_from_extract_and_match",
            }
        )
    elif matching.status == MatchStatus.SKIPPED:
        result = base.model_copy(
            update={
                "status": RouteStatus.REVIEW_REQUIRED,
                "queue": "doc_control",
                "priority": "high",
                "reasons": ["CRM matching was skipped — no entities available for lookup"],
                "next_actions": [
                    "Review the extracted entities",
                    "Re-run extraction and matching steps",
                ],
                "notes": "routing_from_extract_and_match",
            }
        )
    else:
        result = base.model_copy(
            update={
                "status": RouteStatus.FAILED,
                "rejection_reason": "route_unhandled_match_status",
                "notes": f"match_status={matching.status.value}",
            }
        )

    out = JOBS_DIR / job / "routing.json"
    out.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result
