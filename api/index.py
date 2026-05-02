import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web.app import app  # noqa: F401 — Vercel looks for `app`
