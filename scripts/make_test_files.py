"""
Генератор тестовых файлов для папки TEST/.
Запуск из корня проекта:
  .venv\\Scripts\\python scripts/make_test_files.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "TEST"
OUT.mkdir(exist_ok=True)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _build_pdf(lines: list[str]) -> bytes:
    stream_parts = []
    y = 780
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_parts.append(f"BT /F1 10 Tf 45 {y} Td ({safe}) Tj ET")
        y -= 14
        if y < 40:
            break
    stream = "\n".join(stream_parts).encode("latin-1", errors="replace")

    objects: list[bytes] = []

    def obj(body: bytes) -> None:
        objects.append(body)

    obj(b"<< /Type /Catalog /Pages 2 0 R >>")
    obj(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    obj(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
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


# ── Test file 1: FULL SUCCESS — Invoice, INN matched in CRM ─────────────────
INVOICE_NEVA = [
    "=== INVOICE / SCHET-FAKTURA No. 2025-04-117 ===",
    "",
    "Seller:  AO Neva Logistik",
    "INN:     7812014560   KPP: 781201001",
    "Address: St. Petersburg, Nevsky pr. 45, office 301",
    "",
    "Buyer:   OOO PromStroy Group",
    "INN:     7714406582   KPP: 771401001",
    "Address: Moscow, Lenina str. 12",
    "",
    "Invoice date: 15.04.2025",
    "Contract No.: 88/2025 dated 01.03.2025",
    "Payment due:  30.04.2025",
    "",
    "Services rendered in April 2025:",
    "",
    "1. Logistics and freight forwarding      48 750,50 rub.",
    "2. Warehouse handling and storage        12 000,00 rub.",
    "3. Custom clearance support services     64 249,50 rub.",
    "",
    "Subtotal (excl. VAT):  125 000,00 rub.",
    "VAT 20%:                25 000,00 rub.",
    "TOTAL DUE:             150 000,00 rub.",
    "",
    "Bank details:",
    "Bank: Sberbank PJSC, St. Petersburg",
    "BIK: 044030653   Account: 40702810300000012345",
    "",
    "Director: Smirnova M.A. ____________",
    "Chief Accountant: Petrov I.V. ____________",
    "",
    "INN seller: 7812014560   INN buyer: 7714406582",
]

# ── Test file 2: REVIEW REQUIRED — INN not in CRM ──────────────────────────
INVOICE_UNKNOWN = [
    "=== INVOICE No. 2025-03-088 ===",
    "",
    "Seller:  OOO StroiMaterial Plus",
    "INN:     9999012345   KPP: 999901001",
    "Address: Novosibirsk, ul. Kirova 78",
    "",
    "Buyer:   OOO TransAvto",
    "INN:     8812345678   KPP: 881201001",
    "Address: Yekaterinburg, pr. Mira 5",
    "",
    "Invoice date: 10.03.2025",
    "Payment due:  25.03.2025",
    "",
    "Goods supplied:",
    "",
    "1. Cement M500, 10 tons              85 000,00 rub.",
    "2. Reinforcement rebar 12mm, 2 tons  42 500,00 rub.",
    "3. Delivery to site                   7 500,00 rub.",
    "",
    "TOTAL DUE: 135 000,00 rub.",
    "",
    "INN seller: 9999012345   INN buyer: 8812345678",
]

# ── Test file 3: CONTRACT — matched in CRM (Gazprom) ────────────────────────
CONTRACT_GAZPROM = [
    "=== SERVICE AGREEMENT No. 2025/SRV-041 ===",
    "",
    "This Agreement is entered into as of 01.02.2025",
    "",
    "Party A (Customer):",
    "PJSC Gazprom",
    "INN: 7736050003   KPP: 773601001",
    "Location: Moscow, ul. Nametkina 16",
    "",
    "Party B (Contractor):",
    "OOO TechService Group",
    "INN: 5038112233   KPP: 503801001",
    "Location: Moscow, pr. Andropova 22",
    "",
    "Contract period: 01.02.2025 to 31.12.2025",
    "Total contract value: 4 800 000,00 rub.",
    "Monthly payment:        400 000,00 rub.",
    "",
    "Subject: Maintenance and technical support of automated",
    "control systems at production facilities.",
    "",
    "Payment terms: Net 30 from invoice date.",
    "Late payment penalty: 0,1% per day of outstanding amount.",
    "",
    "Signed:",
    "For Party A: _______________   Date: 01.02.2025",
    "For Party B: _______________   Date: 01.02.2025",
    "",
    "INN Party A: 7736050003   INN Party B: 5038112233",
]

# ── Test file 4: Multi-entity rich document ─────────────────────────────────
RICH_DOC = [
    "=== RECONCILIATION ACT No. RA-2025-Q1 ===",
    "",
    "Period: 01.01.2025 - 31.03.2025",
    "",
    "Company A: OOO Yandex",
    "INN: 7743013901",
    "",
    "Company B: AO Megafon",
    "INN: 7841499707",
    "",
    "Transactions in Q1 2025:",
    "",
    "  15.01.2025  Payment for services        320 000,00 rub.",
    "  28.01.2025  Return adjustment            -15 000,00 rub.",
    "  10.02.2025  Monthly subscription fee    120 000,00 rub.",
    "  28.02.2025  Penalty for late delivery     8 500,00 rub.",
    "  05.03.2025  Bulk order processing        245 000,00 rub.",
    "  20.03.2025  Advance payment              100 000,00 rub.",
    "  31.03.2025  Final settlement              52 300,00 rub.",
    "",
    "Total charged:  830 800,00 rub.",
    "Total paid:     830 800,00 rub.",
    "Balance:              0,00 rub.",
    "",
    "Confirmed by:",
    "OOO Yandex: _______________ 31.03.2025",
    "AO Megafon: _______________ 31.03.2025",
    "",
    "INN: 7743013901   INN: 7841499707",
]


def main() -> None:
    files = {
        "01_invoice_CRM_MATCH_full_success.pdf": INVOICE_NEVA,
        "02_invoice_INN_NOT_IN_CRM_review_required.pdf": INVOICE_UNKNOWN,
        "03_contract_gazprom_CRM_MATCH.pdf": CONTRACT_GAZPROM,
        "04_reconciliation_act_multi_entity.pdf": RICH_DOC,
    }
    for name, lines in files.items():
        path = OUT / name
        path.write_bytes(_build_pdf(lines))
        print(f"  Created: {path.name}")

    readme = OUT / "README.txt"
    readme.write_text(
        "DocFlow — Test Files\n"
        "====================\n\n"
        "01_invoice_CRM_MATCH_full_success.pdf\n"
        "  Expected: All 5 pipeline steps GREEN.\n"
        "  INN 7812014560 (AO Neva Logistik) is in CRM.\n"
        "  3 dates, 6 amounts, 2 INN candidates extracted.\n\n"
        "02_invoice_INN_NOT_IN_CRM_review_required.pdf\n"
        "  Expected: Steps 1-4 complete, Route = 'Review required'.\n"
        "  INN 9999012345 is NOT in CRM -> sent to CRM enrichment queue.\n\n"
        "03_contract_gazprom_CRM_MATCH.pdf\n"
        "  Expected: All 5 steps GREEN. Document type = Contract.\n"
        "  INN 7736050003 (PJSC Gazprom) matched.\n\n"
        "04_reconciliation_act_multi_entity.pdf\n"
        "  Expected: All 5 steps GREEN. Rich extraction:\n"
        "  7 dates, 8+ amounts, 2 INN (Yandex + Megafon) both in CRM.\n\n"
        "How to test:\n"
        "  1. Start the server: double-click start_web.vbs\n"
        "  2. Open http://127.0.0.1:8000/\n"
        "  3. Drop any file above into the upload area.\n"
        "  4. Watch the pipeline run step by step.\n",
        encoding="utf-8",
    )
    print(f"  Created: README.txt")
    print(f"\nAll test files saved to: {OUT}")


if __name__ == "__main__":
    main()
