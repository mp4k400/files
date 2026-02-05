from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .config import settings


def ensure_dirs() -> Dict[str, Path]:
    inputs = settings.data_dir / "inputs"
    outputs = settings.data_dir / "outputs"
    metadata = settings.data_dir / "metadata"
    inputs.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    metadata.mkdir(parents=True, exist_ok=True)
    return {"inputs": inputs, "outputs": outputs, "metadata": metadata}


def save_upload(src_path: str, job_id: str, kind: str) -> str:
    paths = ensure_dirs()
    dest = paths["inputs"] / f"{job_id}_{kind}{Path(src_path).suffix}"
    shutil.copy(src_path, dest)
    return str(dest)


def save_metadata(job_id: str, payload: Dict[str, Any]) -> str:
    paths = ensure_dirs()
    dest = paths["metadata"] / f"{job_id}.json"
    payload["saved_at"] = time.time()
    with dest.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    return str(dest)


def save_output_bytes(job_id: str, index: int, content: bytes, ext: str) -> str:
    paths = ensure_dirs()
    dest = paths["outputs"] / f"{job_id}_{index}{ext}"
    with dest.open("wb") as handle:
        handle.write(content)
    return str(dest)


def save_output_file(job_id: str, index: int, source_path: str) -> str:
    paths = ensure_dirs()
    dest = paths["outputs"] / f"{job_id}_{index}{Path(source_path).suffix}"
    shutil.copy(source_path, dest)
    return str(dest)


def local_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return str(Path(path))
