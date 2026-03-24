"""
Проверка цепочки Intake -> Extract -> Match.

Запуск из корня проекта «Агент»:
  .venv\\Scripts\\python scripts/test_three_agents.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.test_two_agents import _minimal_pdf_with_text


def main() -> int:
    from agents.extract.agent import run_extract_by_job_id
    from agents.intake.agent import run_intake
    from agents.match.agent import run_match_by_job_id
    from core.schemas import ExtractionStatus, IngestionStatus, MatchStatus

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

    print("\n=== Match (job_id=%s) ===" % ing.job_id)
    match = run_match_by_job_id(ing.job_id)
    if match is None:
        print("FAIL: match returned None (нет extraction.json?)", file=sys.stderr)
        return 1
    print(match.model_dump_json(indent=2, ensure_ascii=False))
    if match.status != MatchStatus.OK:
        print("FAIL: expected match status ok, got", match.status, file=sys.stderr)
        return 1
    if not match.matches:
        print("FAIL: expected at least one CRM match", file=sys.stderr)
        return 1

    print("\nOK: связка Intake -> Extract -> Match работает.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
