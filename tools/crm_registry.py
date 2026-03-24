from __future__ import annotations

import re

from core.schemas import CRMMatchItem


_CRM_ROWS: dict[str, CRMMatchItem] = {
    "7707083893": CRMMatchItem(
        inn="7707083893",
        company_name="ООО Ромашка",
        account_manager="Иван Петров",
        segment="SMB",
    ),
    "7812014560": CRMMatchItem(
        inn="7812014560",
        company_name="АО Нева Логистик",
        account_manager="Мария Смирнова",
        segment="Mid-Market",
    ),
    "5038112233": CRMMatchItem(
        inn="5038112233",
        company_name="ООО СеверТех",
        account_manager="Алексей Орлов",
        segment="Enterprise",
    ),
}


def normalize_inn(raw: str) -> str:
    digits = re.sub(r"\D+", "", raw or "")
    if len(digits) in (10, 12):
        return digits
    return ""


def lookup_companies_by_inn(values: list[str]) -> tuple[list[str], list[CRMMatchItem]]:
    normalized: list[str] = []
    seen: set[str] = set()
    matches: list[CRMMatchItem] = []
    matched: set[str] = set()

    for raw in values:
        inn = normalize_inn(raw)
        if not inn or inn in seen:
            continue
        seen.add(inn)
        normalized.append(inn)
        row = _CRM_ROWS.get(inn)
        if row is not None and inn not in matched:
            matches.append(row)
            matched.add(inn)
    return normalized, matches
