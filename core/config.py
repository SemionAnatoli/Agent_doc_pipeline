from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
JOBS_DIR = DATA_DIR / "jobs"

ALLOWED_EXTENSIONS = frozenset({".pdf", ".png", ".jpg", ".jpeg"})
MAX_FILE_BYTES = 25 * 1024 * 1024
# If extracted text from first PDF pages is shorter, treat as scan / image-heavy.
MIN_TEXT_CHARS_FOR_NATIVE_PDF = 80
PDF_SAMPLE_PAGES = 3

# Извлечение текста из PDF (агент Extract)
MAX_EXTRACT_PAGES = 40
MAX_EXTRACT_CHARS = 350_000
TEXT_PREVIEW_MAX_CHARS = 900
# Минимум символов текста, чтобы пытаться вытаскивать сущности (ниже — skipped_ocr / пусто).
MIN_TEXT_CHARS_FOR_EXTRACTION = 40
