from __future__ import annotations

import re

from core.schemas import CRMMatchItem


_CRM_ROWS: dict[str, CRMMatchItem] = {
    # Enterprise clients
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
    "7736050003": CRMMatchItem(
        inn="7736050003",
        company_name="ПАО Газпром",
        account_manager="Дмитрий Волков",
        segment="Enterprise",
    ),
    "7702070139": CRMMatchItem(
        inn="7702070139",
        company_name="ПАО Сбербанк",
        account_manager="Елена Захарова",
        segment="Enterprise",
    ),
    "7743013901": CRMMatchItem(
        inn="7743013901",
        company_name="ООО Яндекс",
        account_manager="Сергей Новиков",
        segment="Mid-Market",
    ),
    "7841499707": CRMMatchItem(
        inn="7841499707",
        company_name="АО Мегафон",
        account_manager="Ольга Кузнецова",
        segment="Enterprise",
    ),
    "5261053619": CRMMatchItem(
        inn="5261053619",
        company_name="ООО ТехноПром",
        account_manager="Артём Лебедев",
        segment="SMB",
    ),
    "7705841820": CRMMatchItem(
        inn="7705841820",
        company_name="ООО Авито",
        account_manager="Наталья Морозова",
        segment="Mid-Market",
    ),
    "7714406582": CRMMatchItem(
        inn="7714406582",
        company_name="ООО ВкусВилл",
        account_manager="Павел Козлов",
        segment="SMB",
    ),
    "7830002223": CRMMatchItem(
        inn="7830002223",
        company_name="АО Ленэнерго",
        account_manager="Татьяна Соколова",
        segment="Enterprise",
    ),
    "6671004690": CRMMatchItem(
        inn="6671004690",
        company_name="ООО УралСтрой",
        account_manager="Виктор Попов",
        segment="SMB",
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
