from __future__ import annotations

import json
from pathlib import Path

from core.config import JOBS_DIR
from core.schemas import (
    EmailSendResult,
    EmailSendStatus,
    ExtractionResult,
    MatchStatus,
    MatchingResult,
    RouteStatus,
    RoutingResult,
    TemplateResult,
    TemplateStatus,
)
from tools.email_sender import send_document_email
from tools.extraction_manifest import load_extraction_result
from tools.matching_manifest import load_matching_result
from tools.routing_manifest import load_routing_result


def _build_template_text(job_id: str, extraction: ExtractionResult, matching: MatchingResult, routing: RoutingResult) -> str:
    first_match = matching.matches[0] if matching.matches else None
    company = first_match.company_name if first_match else "Не определено"
    manager = first_match.account_manager if first_match else "Не назначен"
    inn = first_match.inn if first_match else (matching.checked_inn[0] if matching.checked_inn else "Не найден")
    dates = extraction.entities.date_candidates if extraction.entities else []
    sums = extraction.entities.money_candidates if extraction.entities else []
    lines = [
        "Исходящий шаблон документа",
        f"Job ID: {job_id}",
        "",
        "Реквизиты контрагента:",
        f"- Компания: {company}",
        f"- ИНН: {inn}",
        f"- Ответственный менеджер: {manager}",
        "",
        "Извлеченные данные:",
        f"- Даты: {', '.join(dates) if dates else 'нет'}",
        f"- Суммы: {', '.join(sums) if sums else 'нет'}",
        "",
        "Маршрутизация:",
        f"- Статус: {routing.status.value}",
        f"- Очередь: {routing.queue or 'не задана'}",
        f"- Приоритет: {routing.priority or 'не задан'}",
        f"- Причины: {', '.join(routing.reasons) if routing.reasons else 'нет'}",
        "",
        "Следующие шаги:",
    ]
    for action in routing.next_actions:
        lines.append(f"- {action}")
    if not routing.next_actions:
        lines.append("- не указаны")
    return "\n".join(lines) + "\n"


def run_template_by_job_id(job_id: str) -> TemplateResult | None:
    job = job_id.strip()
    extraction = load_extraction_result(job)
    matching = load_matching_result(job)
    routing = load_routing_result(job)
    if extraction is None or matching is None or routing is None:
        return None

    base = TemplateResult(job_id=job, status=TemplateStatus.FAILED)
    if routing.status != RouteStatus.READY_FOR_TEMPLATE:
        result = base.model_copy(
            update={
                "status": TemplateStatus.SKIPPED,
                "rejection_reason": "route_not_ready_for_template",
                "notes": f"route_status={routing.status.value}",
            }
        )
    elif matching.status != MatchStatus.OK:
        result = base.model_copy(
            update={
                "status": TemplateStatus.SKIPPED,
                "rejection_reason": "match_not_ok",
                "notes": f"match_status={matching.status.value}",
            }
        )
    else:
        out = JOBS_DIR / job / "prepared_document.txt"
        out.write_text(
            _build_template_text(job, extraction, matching, routing),
            encoding="utf-8",
        )
        result = TemplateResult(
            job_id=job,
            status=TemplateStatus.READY,
            template_path=str(out),
            notes="template_generated_from_pipeline_results",
        )

    manifest = JOBS_DIR / job / "template.json"
    manifest.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def send_template_by_job_id(job_id: str, recipient_email: str) -> EmailSendResult | None:
    job = job_id.strip()
    recipient = recipient_email.strip()
    template_manifest = JOBS_DIR / job / "template.json"
    if not template_manifest.is_file():
        return None
    doc_path = JOBS_DIR / job / "prepared_document.txt"
    if not doc_path.is_file():
        return None
    subject = f"Документ по задаче {job}"
    body = (
        "Здравствуйте!\n\n"
        "Во вложении подготовленный документ из конвейера обработки.\n\n"
        "С уважением,\n"
        "Document Pipeline Agent"
    )
    ok, note = send_document_email(recipient, subject, body, doc_path)
    result = EmailSendResult(
        job_id=job,
        status=EmailSendStatus.SENT if ok else EmailSendStatus.FAILED,
        recipient_email=recipient,
        subject=subject,
        rejection_reason=None if ok else "smtp_send_failed",
        notes=note,
    )
    out = JOBS_DIR / job / "email_send.json"
    out.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result
