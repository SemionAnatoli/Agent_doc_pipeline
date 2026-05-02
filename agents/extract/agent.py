import json
from pathlib import Path

from core.config import JOBS_DIR, MIN_TEXT_CHARS_FOR_EXTRACTION, TEXT_PREVIEW_MAX_CHARS
from core.schemas import (
    ExtractionResult,
    ExtractionStatus,
    IngestionResult,
    IngestionStatus,
)
from tools.docx_text import extract_docx_plain_text
from tools.entity_patterns import extract_entities_from_text
from tools.pdf_text import extract_pdf_plain_text


def _stored_file_within_jobs(stored: Path) -> bool:
    try:
        stored.resolve().relative_to(JOBS_DIR.resolve())
        return True
    except ValueError:
        return False


def _extract_image_via_groq(path: Path, base: ExtractionResult) -> ExtractionResult:
    """Try Groq vision extraction; fall back to skipped_ocr if unavailable."""
    from tools.groq_vision import extract_entities_from_image, is_groq_available

    if not is_groq_available():
        return base.model_copy(
            update={
                "status": ExtractionStatus.SKIPPED_OCR,
                "text_char_count": 0,
                "notes": "raster_image_requires_ocr_engine (GROQ_API_KEY not set)",
            }
        )
    try:
        entities, raw_preview = extract_entities_from_image(path)
        char_count = sum(
            len(x) for lst in [
                entities.inn_candidates,
                entities.date_candidates,
                entities.money_candidates,
            ] for x in lst
        )
        return base.model_copy(
            update={
                "status": ExtractionStatus.OK,
                "text_char_count": char_count,
                "text_preview": raw_preview,
                "entities": entities,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return base.model_copy(
            update={
                "status": ExtractionStatus.FAILED,
                "rejection_reason": "groq_vision_error",
                "notes": str(exc),
            }
        )


def run_extract(ingestion: IngestionResult) -> ExtractionResult:
    base = ExtractionResult(
        job_id=ingestion.job_id,
        status=ExtractionStatus.FAILED,
        document_kind=ingestion.document_kind,
    )

    if ingestion.status != IngestionStatus.ACCEPTED or not ingestion.stored_path:
        return base.model_copy(
            update={
                "rejection_reason": "intake_not_accepted",
                "notes": "Valid Intake with stored_path required.",
            }
        )

    path = Path(ingestion.stored_path).expanduser().resolve()
    if not _stored_file_within_jobs(path):
        return base.model_copy(
            update={"rejection_reason": "path_outside_jobs_dir", "notes": str(path)}
        )
    if not path.is_file():
        return base.model_copy(
            update={"rejection_reason": "stored_file_missing", "notes": str(path)}
        )

    ext = path.suffix.lower()

    # ── Images: use Groq vision model ────────────────────────────────────────
    if ext in (".png", ".jpg", ".jpeg"):
        result = _extract_image_via_groq(path, base)
        if result.status == ExtractionStatus.OK:
            out = path.parent / "extraction.json"
            out.write_text(
                json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return result

    # ── DOCX: extract via python-docx ─────────────────────────────────────────
    if ext == ".docx":
        try:
            text = extract_docx_plain_text(path)
        except Exception as exc:  # noqa: BLE001
            return base.model_copy(
                update={"rejection_reason": "docx_read_error", "notes": str(exc)}
            )

    # ── PDF: extract text layer ───────────────────────────────────────────────
    elif ext == ".pdf":
        try:
            text = extract_pdf_plain_text(path)
        except Exception as exc:  # noqa: BLE001
            return base.model_copy(
                update={"rejection_reason": "pdf_read_error", "notes": str(exc)}
            )
    else:
        return base.model_copy(
            update={"rejection_reason": f"unsupported_extension:{ext}", "notes": str(path)}
        )

    # ── Text extracted: check length, run regex entities ─────────────────────
    n = len(text.strip())
    if n < MIN_TEXT_CHARS_FOR_EXTRACTION:
        return ExtractionResult(
            job_id=ingestion.job_id,
            status=ExtractionStatus.SKIPPED_OCR,
            document_kind=ingestion.document_kind,
            text_char_count=n,
            text_preview=text[:TEXT_PREVIEW_MAX_CHARS] if text else None,
            notes="insufficient_extracted_text_likely_scan",
        )

    entities = extract_entities_from_text(text)
    result = ExtractionResult(
        job_id=ingestion.job_id,
        status=ExtractionStatus.OK,
        document_kind=ingestion.document_kind,
        text_char_count=n,
        text_preview=text[:TEXT_PREVIEW_MAX_CHARS],
        entities=entities,
    )
    out = path.parent / "extraction.json"
    out.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def run_extract_by_job_id(job_id: str) -> ExtractionResult | None:
    from tools.job_manifest import load_intake_result
    ing = load_intake_result(job_id.strip())
    if ing is None:
        return None
    return run_extract(ing)
