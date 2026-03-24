from pathlib import Path

from pypdf import PdfReader

from core.config import MAX_EXTRACT_CHARS, MAX_EXTRACT_PAGES


def extract_pdf_plain_text(path: Path) -> str:
    """Извлекает текст со страниц PDF с ограничением по страницам и длине."""
    reader = PdfReader(str(path))
    parts: list[str] = []
    total_chars = 0
    for i, page in enumerate(reader.pages):
        if i >= MAX_EXTRACT_PAGES:
            break
        chunk = page.extract_text() or ""
        parts.append(chunk)
        total_chars += len(chunk)
        if total_chars >= MAX_EXTRACT_CHARS:
            break
    joined = "\n".join(parts)
    return joined[:MAX_EXTRACT_CHARS]
