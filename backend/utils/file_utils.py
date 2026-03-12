from pathlib import Path
from uuid import uuid4


def ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def unique_filename(filename: str) -> str:
    ext = Path(filename).suffix
    return f"{uuid4().hex}{ext}"