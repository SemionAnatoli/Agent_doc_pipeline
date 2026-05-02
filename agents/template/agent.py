from __future__ import annotations

import json
from datetime import date
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

_QUEUE_LABELS = {
    "templating": "Ready for delivery",
    "crm_enrichment": "CRM enrichment required",
    "ocr_review": "OCR review required",
    "doc_control": "Document control review",
}

_SEGMENT_LABELS = {
    "SMB": "Small & Medium Business",
    "Mid-Market": "Mid-Market",
    "Enterprise": "Enterprise",
}


def _build_template_text(
    job_id: str,
    extraction: ExtractionResult,
    matching: MatchingResult,
    routing: RoutingResult,
) -> str:
    today = date.today().strftime("%d.%m.%Y")
    first_match = matching.matches[0] if matching.matches else None

    company = first_match.company_name if first_match else "Not identified"
    manager = first_match.account_manager if first_match else "Not assigned"
    segment = _SEGMENT_LABELS.get(first_match.segment, first_match.segment) if first_match and first_match.segment else "—"
    inn = first_match.inn if first_match else (matching.checked_inn[0] if matching.checked_inn else "Not found")

    entities = extraction.entities
    dates = entities.date_candidates if entities else []
    sums = entities.money_candidates if entities else []
    doc_kind = (extraction.document_kind.value if hasattr(extraction.document_kind, "value") else str(extraction.document_kind)).capitalize()

    queue_label = _QUEUE_LABELS.get(routing.queue or "", routing.queue or "—")

    sep = "─" * 60

    lines = [
        "DOCFLOW PIPELINE — PREPARED DOCUMENT",
        sep,
        "",
        f"  Reference:   {job_id}",
        f"  Prepared on: {today}",
        f"  Document type: {doc_kind}",
        "",
        sep,
        "  COUNTERPARTY DETAILS",
        sep,
        f"  Company:         {company}",
        f"  INN:             {inn}",
        f"  Account manager: {manager}",
        f"  Segment:         {segment}",
        "",
        sep,
        "  EXTRACTED DATA",
        sep,
        f"  Dates found:   {', '.join(dates) if dates else 'none'}",
        f"  Amounts found: {', '.join(sums) if sums else 'none'}",
        "",
        sep,
        "  ROUTING DECISION",
        sep,
        f"  Status:   {routing.status.value.replace('_', ' ').title()}",
        f"  Queue:    {queue_label}",
        f"  Priority: {(routing.priority or '—').title()}",
    ]

    if routing.reasons:
        lines.append("")
        lines.append("  Reasons:")
        for r in routing.reasons:
            lines.append(f"    • {r}")

    if routing.next_actions:
        lines.append("")
        lines.append("  Next actions:")
        for a in routing.next_actions:
            lines.append(f"    • {a}")

    lines += [
        "",
        sep,
        "  This document was generated automatically by DocFlow.",
        "  Please do not reply to this message.",
        sep,
        "",
    ]
    return "\n".join(lines)


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

    matching = load_matching_result(job)
    company = "—"
    if matching and matching.matches:
        company = matching.matches[0].company_name

    subject = f"DocFlow — Prepared document for {company} (Job {job[:8]})"
    body = (
        "Hello,\n\n"
        "Please find the prepared document attached.\n\n"
        f"Counterparty: {company}\n"
        f"Job reference: {job}\n\n"
        "This message was generated automatically by DocFlow Pipeline.\n"
        "Please do not reply to this email.\n\n"
        "Best regards,\n"
        "DocFlow Document Processing System"
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
