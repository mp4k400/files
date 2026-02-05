from __future__ import annotations

import os
from pathlib import Path


class Settings:
    base_url: str = os.getenv("WAVESPEED_BASE_URL", "https://api.wavespeed.ai/v1")
    api_key: str | None = os.getenv("WAVESPEED_API_KEY")
    data_dir: Path = Path(os.getenv("WAVESPEED_DATA_DIR", "data")).resolve()
    request_timeout: int = int(os.getenv("WAVESPEED_TIMEOUT", "120"))


settings = Settings()
