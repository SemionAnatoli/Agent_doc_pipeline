"""
Генератор тестовых изображений (PNG / JPG / JPEG) для папки TEST/.
Запуск: .venv\\Scripts\\python scripts/make_image_test_files.py
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "TEST"
OUT.mkdir(exist_ok=True)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont


def get_font(size: int):
    """Try to load a readable font; fall back to default."""
    candidates = [
        "C:/Windows/Fonts/consola.ttf",   # Consolas
        "C:/Windows/Fonts/cour.ttf",       # Courier New
        "C:/Windows/Fonts/arial.ttf",      # Arial
        "C:/Windows/Fonts/calibri.ttf",    # Calibri
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_document(lines: list[tuple[str, int, bool]], width=794, bg="white") -> Image.Image:
    """
    lines: list of (text, font_size, bold)
    Returns a PIL Image.
    """
    img = Image.new("RGB", (width, 1122), color=bg)  # A4 proportion
    draw = ImageDraw.Draw(img)

    y = 40
    for text, size, bold in lines:
        font = get_font(size)
        draw.text((50, y), text, fill="black", font=font)
        # approximate line height
        y += size + 6
        if y > 1080:
            break

    # thin border
    draw.rectangle([10, 10, width - 10, 1112], outline="#999999", width=1)
    return img


# ── Image 1: PNG invoice — INN in CRM (Газпром) ─────────────────────────────
INVOICE_PNG_LINES = [
    ("INVOICE / SCHET No. 2025-04-215", 18, True),
    ("", 6, False),
    ("Seller:", 11, True),
    ("PJSC Gazprom", 13, True),
    ("INN: 7736050003    KPP: 773601001", 12, False),
    ("Address: Moscow, ul. Nametkina 16, bld. 1", 11, False),
    ("Phone: +7 (495) 719-30-01", 11, False),
    ("", 6, False),
    ("Buyer:", 11, True),
    ("OOO TechService Group", 13, True),
    ("INN: 5038112233    KPP: 503801001", 12, False),
    ("Address: Moscow, pr. Andropova 22", 11, False),
    ("", 6, False),
    ("─" * 72, 10, False),
    ("Invoice date:  15.03.2025", 12, False),
    ("Contract No.:  GZ-2025/SRV-041 dated 01.01.2025", 12, False),
    ("Payment due:   30.03.2025", 12, False),
    ("─" * 72, 10, False),
    ("", 6, False),
    ("SERVICES RENDERED:", 12, True),
    ("", 4, False),
    ("1. Pipeline monitoring system maintenance     185 000,00 rub.", 11, False),
    ("2. Remote diagnostic support (March 2025)      95 000,00 rub.", 11, False),
    ("3. Software update & licensing                 62 500,00 rub.", 11, False),
    ("4. On-site engineer visits (3 days)            37 500,00 rub.", 11, False),
    ("", 6, False),
    ("─" * 72, 10, False),
    ("Subtotal (excl. VAT):        380 000,00 rub.", 12, False),
    ("VAT 20%:                      76 000,00 rub.", 12, False),
    ("TOTAL DUE:                   456 000,00 rub.", 14, True),
    ("─" * 72, 10, False),
    ("", 6, False),
    ("Bank: Gazprombank, Moscow", 11, False),
    ("BIK: 044525823   Account: 40702810638000012345", 11, False),
    ("", 8, False),
    ("Director: Miller A.B.  _______________   15.03.2025", 11, False),
    ("Chief Accountant: Semenova T.V.  _______________", 11, False),
    ("", 8, False),
    ("INN Seller: 7736050003    INN Buyer: 5038112233", 11, False),
]

# ── Image 2: JPG invoice — INN NOT in CRM → review required ─────────────────
INVOICE_JPG_LINES = [
    ("INVOICE No. 2025-03-077", 18, True),
    ("", 6, False),
    ("Seller:", 11, True),
    ("OOO StroiMontazh Plus", 13, True),
    ("INN: 6311045678    KPP: 631101001", 12, False),
    ("Address: Samara, ul. Novo-Sadovaya 106", 11, False),
    ("", 6, False),
    ("Buyer:", 11, True),
    ("IP Voronov Alexey Petrovich", 13, True),
    ("INN: 631100234567   ", 12, False),
    ("Address: Samara, ul. Moskovskoe sh. 34, apt 12", 11, False),
    ("", 6, False),
    ("─" * 72, 10, False),
    ("Invoice date:  22.03.2025", 12, False),
    ("Payment due:   05.04.2025", 12, False),
    ("─" * 72, 10, False),
    ("", 6, False),
    ("GOODS SUPPLIED:", 12, True),
    ("", 4, False),
    ("1. Steel pipe 219x8mm, 50m               42 500,00 rub.", 11, False),
    ("2. Steel pipe 159x6mm, 80m               38 400,00 rub.", 11, False),
    ("3. Flanges DN200 (set of 10)             12 000,00 rub.", 11, False),
    ("4. Welding electrodes UONI 4mm, 20kg      3 600,00 rub.", 11, False),
    ("5. Delivery to construction site          3 500,00 rub.", 11, False),
    ("", 6, False),
    ("─" * 72, 10, False),
    ("Subtotal:                    100 000,00 rub.", 12, False),
    ("VAT 20%:                      20 000,00 rub.", 12, False),
    ("TOTAL DUE:                   120 000,00 rub.", 14, True),
    ("─" * 72, 10, False),
    ("", 8, False),
    ("Director: Voronov A.P.  _______________   22.03.2025", 11, False),
    ("", 8, False),
    ("INN Seller: 6311045678    INN Buyer: 631100234567", 11, False),
]

# ── Image 3: JPEG act — two INNs both in CRM (Яндекс + Авито) ───────────────
ACT_JPEG_LINES = [
    ("RECONCILIATION ACT No. RA-2025-02", 18, True),
    ("Period: 01.02.2025 — 28.02.2025", 13, False),
    ("", 6, False),
    ("Company A:", 11, True),
    ("OOO Yandex", 13, True),
    ("INN: 7743013901    KPP: 774301001", 12, False),
    ("", 4, False),
    ("Company B:", 11, True),
    ("OOO Avito", 13, True),
    ("INN: 7705841820    KPP: 770501001", 12, False),
    ("", 6, False),
    ("─" * 72, 10, False),
    ("TRANSACTIONS IN FEBRUARY 2025:", 12, True),
    ("", 4, False),
    ("03.02.2025  Advertising placement (Jan)         320 000,00 rub.", 11, False),
    ("10.02.2025  Promo campaign - automotive          85 000,00 rub.", 11, False),
    ("14.02.2025  Banner placement Q1                  48 500,00 rub.", 11, False),
    ("21.02.2025  Real estate listings package         72 000,00 rub.", 11, False),
    ("28.02.2025  Final settlement February            24 500,00 rub.", 11, False),
    ("", 6, False),
    ("─" * 72, 10, False),
    ("Total charged:    550 000,00 rub.", 12, False),
    ("Total paid:       550 000,00 rub.", 12, False),
    ("Balance:                0,00 rub.", 12, True),
    ("─" * 72, 10, False),
    ("", 8, False),
    ("OOO Yandex:  _______________   28.02.2025", 11, False),
    ("OOO Avito:   _______________   28.02.2025", 11, False),
    ("", 8, False),
    ("INN: 7743013901    INN: 7705841820", 11, False),
]


def save_image(lines, filename, fmt="PNG", quality=95):
    img = draw_document(lines)
    path = OUT / filename
    if fmt == "JPEG":
        img.save(str(path), format="JPEG", quality=quality)
    else:
        img.save(str(path), format=fmt)
    size_kb = path.stat().st_size // 1024
    print(f"  Created: {filename}  ({size_kb} KB)")


if __name__ == "__main__":
    save_image(INVOICE_PNG_LINES,  "07_invoice_PNG_gazprom_CRM_match.png",  "PNG")
    save_image(INVOICE_JPG_LINES,  "08_invoice_JPG_unknown_INN_review.jpg",  "JPEG")
    save_image(ACT_JPEG_LINES,     "09_act_JPEG_yandex_avito_CRM_match.jpeg", "JPEG")
    print(f"\nImage test files saved to: {OUT}")
    print("\nExpected pipeline results (Groq Vision processes images):")
    print("  07_invoice_PNG_gazprom_CRM_match.png    -> All 5 steps GREEN")
    print("  08_invoice_JPG_unknown_INN_review.jpg   -> Route: Review required")
    print("  09_act_JPEG_yandex_avito_CRM_match.jpeg -> All 5 steps GREEN, 2 companies")
