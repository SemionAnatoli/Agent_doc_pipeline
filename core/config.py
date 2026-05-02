import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# On Vercel the filesystem is read-only except /tmp
if os.getenv("VERCEL"):
    DATA_DIR = Path("/tmp/docflow_data")
else:
    DATA_DIR = PROJECT_ROOT / "data"

JOBS_DIR = DATA_DIR / "jobs"

ALLOWED_EXTENSIONS = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".docx"})
MAX_FILE_BYTES = 25 * 1024 * 1024

MIN_TEXT_CHARS_FOR_NATIVE_PDF = 80
PDF_SAMPLE_PAGES = 3

MAX_EXTRACT_PAGES = 40
MAX_EXTRACT_CHARS = 350_000
TEXT_PREVIEW_MAX_CHARS = 900
MIN_TEXT_CHARS_FOR_EXTRACTION = 40
