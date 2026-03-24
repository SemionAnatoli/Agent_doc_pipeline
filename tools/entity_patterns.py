import re

from core.schemas import ExtractedEntities


def _unique_preserve(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in seq:
        k = x.strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out


def extract_entities_from_text(text: str) -> ExtractedEntities:
    """Простые regex по русским документам (ИНН, даты, суммы). Без LLM."""
    inn_set: set[str] = set()
    for m in re.finditer(r"(?<!\d)(\d{10}|\d{12})(?!\d)", text):
        inn_set.add(m.group(1))

    dates: list[str] = []
    for m in re.finditer(
        r"\b(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}\b",
        text,
    ):
        dates.append(m.group(0))

    money: list[str] = []
    money_re = re.compile(
        r"(?:\d{1,3}(?:\s\d{3})+|\d+)\s*[.,]\s*\d{2}(?:\s*(?:руб|руб\.|₽|RUB))?",
        re.IGNORECASE,
    )
    for m in money_re.finditer(text):
        money.append(m.group(0).strip())

    return ExtractedEntities(
        inn_candidates=sorted(inn_set),
        date_candidates=_unique_preserve(dates)[:25],
        money_candidates=_unique_preserve(money)[:40],
    )
