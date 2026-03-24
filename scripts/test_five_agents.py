"""
Проверка цепочки Intake -> Extract -> Match -> Route -> Template.

Запуск из корня проекта «Агент»:
  .venv\\Scripts\\python scripts/test_five_agents.py
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
    from agents.route.agent import run_route_by_job_id
    from agents.template.agent import run_template_by_job_id
    from core.schemas import ExtractionStatus, IngestionStatus, MatchStatus, RouteStatus, TemplateStatus

    out_dir = ROOT / "data" / "_test_run"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "schet_demo.pdf"
    pdf_path.write_bytes(_minimal_pdf_with_text())

    ing = run_intake(pdf_path)
    if ing.status != IngestionStatus.ACCEPTED:
        print("FAIL: intake not accepted", file=sys.stderr)
        return 1

    ext = run_extract_by_job_id(ing.job_id)
    if ext is None or ext.status != ExtractionStatus.OK:
        print("FAIL: extract not ok", file=sys.stderr)
        return 1

    match = run_match_by_job_id(ing.job_id)
    if match is None or match.status not in (MatchStatus.OK, MatchStatus.NO_MATCH):
        print("FAIL: unexpected match status", file=sys.stderr)
        return 1

    route = run_route_by_job_id(ing.job_id)
    if route is None or route.status not in (RouteStatus.READY_FOR_TEMPLATE, RouteStatus.REVIEW_REQUIRED):
        print("FAIL: unexpected route status", file=sys.stderr)
        return 1

    templ = run_template_by_job_id(ing.job_id)
    if templ is None:
        print("FAIL: template returned None", file=sys.stderr)
        return 1
    print(templ.model_dump_json(indent=2, ensure_ascii=False))
    if templ.status != TemplateStatus.READY:
        print("FAIL: expected template ready, got", templ.status, file=sys.stderr)
        return 1
    print("OK: связка Intake -> Extract -> Match -> Route -> Template работает.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
