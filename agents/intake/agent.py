import json
from pathlib import Path

from core.config import ALLOWED_EXTENSIONS, MAX_FILE_BYTES
from core.schemas import DocumentKind, IngestionResult, IngestionStatus
from tools.docx_text import count_docx_pages, extract_docx_plain_text
from tools.pdf_inspect import inspect_pdf
from tools.storage import new_job_id, store_upload


def _classify_from_filename(name: str) -> tuple[DocumentKind, float]:
    lower = name.lower()
    invoice_markers = (
        "invoice",
        "inv_",
        "inv-",
        "bill",
        "счет",
        "счёт",
        "накладная",
        "factura",
        "sf_",
    )
    contract_markers = (
        "contract",
        "договор",
        "agreement",
        "appendix",
        "приложение",
    )
    for m in invoice_markers:
        if m in lower:
            return DocumentKind.INVOICE, 0.75
    for m in contract_markers:
        if m in lower:
            return DocumentKind.CONTRACT, 0.75
    return DocumentKind.UNKNOWN, 0.35


def run_intake(source_path: Path) -> IngestionResult:
    """
    Validate input, persist under data/jobs/{job_id}/, classify coarse document kind,
    detect whether OCR is likely needed (PDF text layer / raster images).
    """
    path = source_path.expanduser().resolve()
    job_id = new_job_id()
    filename = path.name

    if not path.is_file():
        return IngestionResult(
            job_id=job_id,
            status=IngestionStatus.REJECTED,
            original_filename=filename,
            rejection_reason="file_not_found",
        )

    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return IngestionResult(
            job_id=job_id,
            status=IngestionStatus.REJECTED,
            original_filename=filename,
            rejection_reason=f"unsupported_extension:{ext or '(none)'}",
        )

    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        return IngestionResult(
            job_id=job_id,
            status=IngestionStatus.REJECTED,
            original_filename=filename,
            rejection_reason="file_too_large",
            notes=f"size_bytes={size}",
        )

    kind, confidence = _classify_from_filename(filename)
    page_count: int | None = None
    needs_ocr = False
    notes_parts: list[str] = []

    if ext == ".pdf":
        try:
            page_count, needs_ocr, pdf_note = inspect_pdf(path)
            notes_parts.append(pdf_note)
        except Exception as exc:  # noqa: BLE001 — surface as rejected job
            return IngestionResult(
                job_id=job_id,
                status=IngestionStatus.REJECTED,
                original_filename=filename,
                rejection_reason="pdf_read_error",
                notes=str(exc),
            )
    elif ext == ".docx":
        try:
            page_count = count_docx_pages(path)
            needs_ocr = False
            notes_parts.append("docx_native_text")
        except Exception as exc:  # noqa: BLE001
            return IngestionResult(
                job_id=job_id,
                status=IngestionStatus.REJECTED,
                original_filename=filename,
                rejection_reason="docx_read_error",
                notes=str(exc),
            )
    else:
        page_count = 1
        needs_ocr = True
        notes_parts.append("raster_image_assumed_scan")

    if kind == DocumentKind.UNKNOWN:
        kind = DocumentKind.OTHER
        confidence = max(confidence, 0.25)

    stored = store_upload(path, job_id)

    result = IngestionResult(
        job_id=job_id,
        status=IngestionStatus.ACCEPTED,
        original_filename=filename,
        stored_path=str(stored),
        document_kind=kind,
        kind_confidence=confidence,
        needs_ocr=needs_ocr,
        page_count=page_count,
        notes="; ".join(notes_parts) if notes_parts else None,
    )
    manifest = stored.parent / "intake.json"
    manifest.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result
