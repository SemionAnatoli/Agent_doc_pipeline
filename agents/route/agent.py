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
                "reasons": [f"extract_status={extraction.status.value}"],
                "next_actions": ["Проверить качество входного файла", "Добавить OCR-обработку"],
                "notes": "routing_from_extract_and_match",
            }
        )
    elif matching.status == MatchStatus.OK:
        reasons = ["crm_match_found"]
        if len(matching.checked_inn) > 1:
            reasons.append("multiple_inn_candidates")
        result = base.model_copy(
            update={
                "status": RouteStatus.READY_FOR_TEMPLATE,
                "queue": "templating",
                "priority": "normal",
                "reasons": reasons,
                "next_actions": ["Сформировать исходящий шаблон документа", "Передать в канал отправки"],
                "notes": "routing_from_extract_and_match",
            }
        )
    elif matching.status == MatchStatus.NO_MATCH:
        result = base.model_copy(
            update={
                "status": RouteStatus.REVIEW_REQUIRED,
                "queue": "crm_enrichment",
                "priority": "high",
                "reasons": ["crm_match_not_found"],
                "next_actions": ["Проверить ИНН вручную", "Добавить/обновить контрагента в CRM"],
                "notes": "routing_from_extract_and_match",
            }
        )
    elif matching.status == MatchStatus.SKIPPED:
        result = base.model_copy(
            update={
                "status": RouteStatus.REVIEW_REQUIRED,
                "queue": "doc_control",
                "priority": "high",
                "reasons": [f"match_status={matching.status.value}"],
                "next_actions": ["Проверить извлечённые сущности", "Повторить Extract/Match"],
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
