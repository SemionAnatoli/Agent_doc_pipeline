import shutil
import uuid
from pathlib import Path

from core.config import JOBS_DIR


def new_job_id() -> str:
    return str(uuid.uuid4())


def ensure_job_dir(job_id: str) -> Path:
    path = JOBS_DIR / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def store_upload(source: Path, job_id: str) -> Path:
    """Copy source file into data/jobs/{job_id}/ preserving extension."""
    dest_dir = ensure_job_dir(job_id)
    ext = source.suffix.lower() or ".bin"
    dest = dest_dir / f"original{ext}"
    shutil.copy2(source, dest)
    return dest
