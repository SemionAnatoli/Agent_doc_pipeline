"""
Генерация демонстрационного PDF-счёта для тестирования полного пайплайна.
ИНН 7812014560 есть в CRM → пайплайн должен пройти все 5 шагов.

Запуск из корня проекта:
  .venv\\Scripts\\python scripts/make_demo_pdf.py
Файл сохраняется в: data/_test_run/schet_neva_logistik.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _build_pdf(lines_text: list[str]) -> bytes:
    """Минимальный валидный PDF с текстом (без сторонних пакетов)."""
    # Кодируем строки как PDF stream с позиционированием
    stream_parts = []
    y = 750
    for line in lines_text:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_parts.append(f"BT /F1 11 Tf 50 {y} Td ({safe}) Tj ET")
        y -= 16
        if y < 50:
            break

    stream = "\n".join(stream_parts).encode("latin-1", errors="replace")

    objects: list[bytes] = []

    def obj(body: bytes) -> None:
        objects.append(body)

    obj(b"<< /Type /Catalog /Pages 2 0 R >>")
    obj(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    obj(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    obj(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
    obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    parts: list[bytes] = [b"%PDF-1.4\n"]
    offsets: list[int] = [0]
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


INVOICE_LINES = [
    "SCHET-FAKTURA No. 2025-04-117",
    "Date: 15.04.2025",
    "",
    "Seller:",
    "AO Neva Logistik",
    "INN 7812014560  KPP 781201001",
    "Address: St. Petersburg, Nevsky pr. 45, office 301",
    "Bank: Sberbank, BIK 044030653",
    "",
    "Buyer:",
    "OOO PromStroy Group",
    "INN 7714406582  KPP 771401001",
    "Address: Moscow, ul. Lenina 12",
    "",
    "Services rendered under contract No. 88/2025 dated 01.03.2025:",
    "",
    "1. Logistics services (April 2025)    48 750,50 rub.",
    "2. Warehouse handling fee             12 000,00 rub.",
    "3. Custom clearance support           64 249,50 rub.",
    "",
    "Subtotal: 125 000,00 rub.",
    "VAT (20%):  25 000,00 rub.",
    "TOTAL DUE: 150 000,00 rub.",
    "",
    "Payment due: 30.04.2025",
    "",
    "Director: Smirnova M.A.",
    "Chief accountant: Petrov I.V.",
    "",
    "Contract reference: 88/2025 of 01.03.2025",
    "INN seller: 7812014560",
    "INN buyer:  7714406582",
]


def main() -> None:
    out_dir = ROOT / "data" / "_test_run"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "schet_neva_logistik.pdf"
    out_path.write_bytes(_build_pdf(INVOICE_LINES))
    print(f"Demo PDF saved: {out_path}")
    print("Upload this file to test the full pipeline (all 5 steps should succeed).")
    print("INN 7812014560 → AO Neva Logistik [Mid-Market] — exists in CRM.")


if __name__ == "__main__":
    main()
