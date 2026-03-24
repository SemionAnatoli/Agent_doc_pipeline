import json
from pathlib import Path

from core.config import JOBS_DIR, MIN_TEXT_CHARS_FOR_EXTRACTION, TEXT_PREVIEW_MAX_CHARS
from core.schemas import (
    ExtractionResult,
    ExtractionStatus,
    IngestionResult,
    IngestionStatus,
)
from tools.entity_patterns import extract_entities_from_text
from tools.pdf_text import extract_pdf_plain_text


def _stored_file_within_jobs(stored: Path) -> bool:
    try:
        stored.resolve().relative_to(JOBS_DIR.resolve())
        return True
    except ValueError:
        return False


def run_extract(ingestion: IngestionResult) -> ExtractionResult:
    """
    Второй агент: из текста PDF (без OCR) вытаскивает кандидаты ИНН / даты / суммы.
    Растровые вложения и «пустой» PDF → skipped_ocr.
    """
    base = ExtractionResult(
        job_id=ingestion.job_id,
        status=ExtractionStatus.FAILED,
        document_kind=ingestion.document_kind,
    )

    if ingestion.status != IngestionStatus.ACCEPTED or not ingestion.stored_path:
        return base.model_copy(
            update={
                "rejection_reason": "intake_not_accepted",
                "notes": "Нужен успешный Intake с stored_path.",
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
    if ext in (".png", ".jpg", ".jpeg"):
        return ExtractionResult(
            job_id=ingestion.job_id,
            status=ExtractionStatus.SKIPPED_OCR,
            document_kind=ingestion.document_kind,
            text_char_count=0,
            notes="raster_image_requires_ocr_engine",
        )

    if ext != ".pdf":
        return base.model_copy(
            update={"rejection_reason": f"unsupported_extension:{ext}", "notes": str(path)}
        )

    try:
        text = extract_pdf_plain_text(path)
    except Exception as exc:  # noqa: BLE001
        return base.model_copy(
            update={"rejection_reason": "pdf_read_error", "notes": str(exc)}
        )

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
    preview = text[:TEXT_PREVIEW_MAX_CHARS]
    result = ExtractionResult(
        job_id=ingestion.job_id,
        status=ExtractionStatus.OK,
        document_kind=ingestion.document_kind,
        text_char_count=n,
        text_preview=preview,
        entities=entities,
    )

    out = path.parent / "extraction.json"
    out.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def run_extract_by_job_id(job_id: str) -> ExtractionResult | None:
    """Загружает intake.json из data/jobs/{job_id}/ и запускает извлечение."""
    from tools.job_manifest import load_intake_result

    ing = load_intake_result(job_id.strip())
    if ing is None:
        return None
    return run_extract(ing)
