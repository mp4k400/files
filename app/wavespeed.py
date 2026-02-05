from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests

from .config import settings


class WaveSpeedError(RuntimeError):
    pass


class WaveSpeedClient:
    def __init__(self) -> None:
        self.base_url = settings.base_url.rstrip("/")
        self.timeout = settings.request_timeout
        self.session = requests.Session()
        if settings.api_key:
            self.session.headers.update({"Authorization": f"Bearer {settings.api_key}"})

    def _raise_for_status(self, response: requests.Response) -> None:
        if not response.ok:
            raise WaveSpeedError(
                f"WaveSpeed API error {response.status_code}: {response.text}"
            )

    def list_models(self) -> List[Dict[str, Any]]:
        response = self.session.get(f"{self.base_url}/models", timeout=self.timeout)
        self._raise_for_status(response)
        payload = response.json()
        return payload.get("data", payload)

    def upload_file(self, file_path: str) -> str:
        with open(file_path, "rb") as handle:
            files = {"file": handle}
            response = self.session.post(
                f"{self.base_url}/files", files=files, timeout=self.timeout
            )
        self._raise_for_status(response)
        payload = response.json()
        return payload.get("id") or payload.get("file_id")

    def submit_generation(self, model_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/generate/{model_id}",
            json=payload,
            timeout=self.timeout,
        )
        self._raise_for_status(response)
        return response.json()

    def poll_job(self, job_id: str) -> Dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}/jobs/{job_id}", timeout=self.timeout
        )
        self._raise_for_status(response)
        return response.json()

    def download_file(self, url: str) -> bytes:
        response = self.session.get(url, timeout=self.timeout)
        self._raise_for_status(response)
        return response.content

    def wait_for_completion(
        self, job_id: str, poll_interval: float = 2.5, timeout: float = 600
    ) -> Dict[str, Any]:
        start = time.time()
        while True:
            payload = self.poll_job(job_id)
            status = payload.get("status")
            if status in {"succeeded", "failed", "canceled"}:
                return payload
            if time.time() - start > timeout:
                raise WaveSpeedError("Timed out waiting for job completion")
            time.sleep(poll_interval)


def build_generation_payload(
    prompt: str,
    image_file_id: Optional[str],
    video_file_id: Optional[str],
    params: Dict[str, Any],
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"prompt": prompt}
    if image_file_id:
        payload["image"] = image_file_id
    if video_file_id:
        payload["video"] = video_file_id
    payload.update(params)
    return payload
