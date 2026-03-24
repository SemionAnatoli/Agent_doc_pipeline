"""
Проверка цепочки Intake -> Extract: пишется минимальный PDF с текстом (без сторонних пакетов),
затем run_intake и run_extract_by_job_id.

Запуск из корня проекта «Агент»:
  .venv\\Scripts\\python scripts/test_two_agents.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _minimal_pdf_with_text() -> bytes:
    """Одиночная страница, Helvetica, строка с ИНН, датой и суммой (ASCII)."""
    # Длина извлечённого текста должна быть >= MIN_TEXT_CHARS_FOR_EXTRACTION (40).
    lines = [
        "BT /F1 12 Tf 72 720 Td (INN 7707083893 15.03.2025 12 345,67 RUB ok) Tj ET",
    ]
    stream = "\n".join(lines).encode("latin-1")
    objects: list[bytes] = []

    def obj(body: bytes) -> None:
        objects.append(body)

    obj(b"<< /Type /Catalog /Pages 2 0 R >>")
    obj(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    obj(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    obj(
        b"<< /Length %d >>\nstream\n" % len(stream)
        + stream
        + b"\nendstream"
    )
    obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    parts: list[bytes] = [b"%PDF-1.4\n"]
    offsets = [0]
    pos = len(parts[0])
    for i, body in enumerate(objects, start=1):
        chunk = b"%d 0 obj\n" % i + body + b"\nendobj\n"
        offsets.append(pos)
        parts.append(chunk)
        pos += len(chunk)

    xref_pos = pos
    parts.append(b"xref\n0 %d\n" % (len(objects) + 1))
    parts.append(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        parts.append(b"%010d 00000 n \n" % off)
    parts.append(
        b"trailer<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF"
        % (len(objects) + 1, xref_pos)
    )
    return b"".join(parts)


def main() -> int:
    from agents.extract.agent import run_extract_by_job_id
    from agents.intake.agent import run_intake
    from core.schemas import ExtractionStatus, IngestionStatus

    out_dir = ROOT / "data" / "_test_run"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "schet_demo.pdf"
    pdf_path.write_bytes(_minimal_pdf_with_text())

    print("=== Intake ===")
    ing = run_intake(pdf_path)
    print(ing.model_dump_json(indent=2, ensure_ascii=False))
    if ing.status != IngestionStatus.ACCEPTED:
        print("FAIL: intake not accepted", file=sys.stderr)
        return 1

    print("\n=== Extract (job_id=%s) ===" % ing.job_id)
    ext = run_extract_by_job_id(ing.job_id)
    if ext is None:
        print("FAIL: extract returned None (нет intake.json?)", file=sys.stderr)
        return 1
    print(ext.model_dump_json(indent=2, ensure_ascii=False))

    if ext.status != ExtractionStatus.OK:
        print("FAIL: expected extract status ok, got", ext.status, file=sys.stderr)
        return 1
    if not ext.entities or "7707083893" not in ext.entities.inn_candidates:
        print("FAIL: INN not in entities", file=sys.stderr)
        return 1

    print("\nOK: связка Intake -> Extract работает.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
