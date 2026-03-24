from pathlib import Path

from pypdf import PdfReader

from core.config import MIN_TEXT_CHARS_FOR_NATIVE_PDF, PDF_SAMPLE_PAGES


def inspect_pdf(path: Path) -> tuple[int, bool, str]:
    """
    Returns (page_count, needs_ocr, note).
    needs_ocr is True when little extractable text (likely scan).
    """
    reader = PdfReader(str(path))
    page_count = len(reader.pages)
    if page_count == 0:
        return 0, True, "empty_pdf"

    sample_pages = min(PDF_SAMPLE_PAGES, page_count)
    chunks: list[str] = []
    for i in range(sample_pages):
        text = reader.pages[i].extract_text() or ""
        chunks.append(text)
    joined = "\n".join(chunks).strip()
    char_count = len(joined)
    needs = char_count < MIN_TEXT_CHARS_FOR_NATIVE_PDF
    note = f"sample_text_chars={char_count}"
    return page_count, needs, note
