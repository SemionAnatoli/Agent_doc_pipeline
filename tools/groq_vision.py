from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path

from core.schemas import ExtractedEntities

_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

_PROMPT = """You are a document data extraction assistant.
Analyze this document image and extract all structured data.

Return ONLY a valid JSON object — no explanations, no markdown fences:
{
  "inn_candidates": ["10 or 12-digit INN/TIN numbers found"],
  "date_candidates": ["dates in DD.MM.YYYY format"],
  "money_candidates": ["monetary amounts with currency, e.g. 48 750,50 rub."]
}

Rules:
- inn_candidates: only sequences of exactly 10 or 12 consecutive digits that look like tax IDs
- date_candidates: only full dates DD.MM.YYYY (day 01-31, month 01-12, year 19xx or 20xx)
- money_candidates: numbers with comma/dot separator and currency unit (rub, руб, RUB, ₽)
- If nothing found for a field, use an empty list []
"""


def _groq_client():
    from groq import Groq
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY not set in .env")
    return Groq(api_key=key)


def _image_to_base64(path: Path) -> tuple[str, str]:
    """Return (base64_data, media_type)."""
    ext = path.suffix.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    data = base64.standard_b64encode(path.read_bytes()).decode()
    return data, f"image/{ext}"


def _parse_entities(raw: str) -> ExtractedEntities:
    """Extract JSON from model response and build ExtractedEntities."""
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return ExtractedEntities(inn_candidates=[], date_candidates=[], money_candidates=[])
    try:
        obj = json.loads(match.group())
    except json.JSONDecodeError:
        return ExtractedEntities(inn_candidates=[], date_candidates=[], money_candidates=[])

    def clean(lst) -> list[str]:
        if not isinstance(lst, list):
            return []
        return [str(x).strip() for x in lst if str(x).strip()]

    return ExtractedEntities(
        inn_candidates=clean(obj.get("inn_candidates", [])),
        date_candidates=clean(obj.get("date_candidates", [])),
        money_candidates=clean(obj.get("money_candidates", [])),
    )


def extract_entities_from_image(image_path: Path) -> tuple[ExtractedEntities, str]:
    """
    Send image to Groq vision model and extract INN/dates/money.
    Returns (entities, extracted_text_repr).
    Raises RuntimeError if API key missing or request fails.
    """
    client = _groq_client()
    b64, media_type = _image_to_base64(image_path)

    response = client.chat.completions.create(
        model=_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{b64}"},
                    },
                    {"type": "text", "text": _PROMPT},
                ],
            }
        ],
        max_tokens=1024,
        temperature=0.1,
    )

    raw = response.choices[0].message.content or ""
    entities = _parse_entities(raw)
    return entities, raw[:500]


def is_groq_available() -> bool:
    """Check if GROQ_API_KEY is configured."""
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    except ImportError:
        pass
    return bool(os.getenv("GROQ_API_KEY", "").strip())
