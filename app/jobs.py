from __future__ import annotations

import threading
import time
from queue import Queue
from typing import Dict, Optional

from .models import JobCreateRequest, JobRecord, JobStatus
from .storage import save_metadata, save_output_bytes, save_output_file, save_upload
from .wavespeed import WaveSpeedClient, build_generation_payload


class JobManager:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = threading.Lock()
        self._queue: Queue[JobRecord] = Queue()
        self._client = WaveSpeedClient()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def submit(self, request: JobCreateRequest) -> JobRecord:
        now = time.time()
        job = JobRecord(
            model_id=request.model_id,
            prompt=request.prompt,
            created_at=now,
            updated_at=now,
            extra_params=request.extra_params,
        )
        if request.image_path:
            job.input_files["image"] = save_upload(request.image_path, job.id, "image")
        if request.video_path:
            job.input_files["video"] = save_upload(request.video_path, job.id, "video")
        with self._lock:
            self._jobs[job.id] = job
        self._queue.put(job)
        return job

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

    def _run(self) -> None:
        while True:
            job = self._queue.get()
            try:
                self._execute(job)
            except Exception as exc:  # pragma: no cover - defensive
                self._update(job, JobStatus.failed, message=str(exc))
            finally:
                self._queue.task_done()

    def _execute(self, job: JobRecord) -> None:
        self._update(job, JobStatus.running, progress=0.05)
        image_id = None
        video_id = None
        if job.input_files.get("image"):
            image_id = self._client.upload_file(job.input_files["image"])
        if job.input_files.get("video"):
            video_id = self._client.upload_file(job.input_files["video"])
        payload = build_generation_payload(
            job.prompt, image_id, video_id, job.extra_params
        )
        response = self._client.submit_generation(job.model_id, payload)
        job.remote_job_id = response.get("job_id") or response.get("id")
        self._update(job, JobStatus.running, progress=0.2)
        if not job.remote_job_id:
            raise RuntimeError("WaveSpeed did not return a job id")
        result = self._client.wait_for_completion(job.remote_job_id)
        status = result.get("status")
        if status != "succeeded":
            raise RuntimeError(result.get("error", "WaveSpeed job failed"))
        outputs = result.get("outputs") or result.get("output_urls") or []
        for index, output in enumerate(outputs, start=1):
            if isinstance(output, dict):
                url = output.get("url")
            else:
                url = output
            if not url:
                continue
            content = self._client.download_file(url)
            ext = ".bin"
            if isinstance(url, str) and "." in url:
                ext = "." + url.split(".")[-1].split("?")[0]
            output_path = save_output_bytes(job.id, index, content, ext)
            job.output_files.append(output_path)
        metadata = {
            "model_id": job.model_id,
            "prompt": job.prompt,
            "inputs": job.input_files,
            "outputs": job.output_files,
            "remote_job_id": job.remote_job_id,
            "extra_params": job.extra_params,
        }
        job.metadata_path = save_metadata(job.id, metadata)
        self._update(job, JobStatus.succeeded, progress=1.0)

    def _update(
        self,
        job: JobRecord,
        status: JobStatus,
        progress: Optional[float] = None,
        message: Optional[str] = None,
    ) -> None:
        with self._lock:
            job.status = status
            job.updated_at = time.time()
            if progress is not None:
                job.progress = progress
            if message:
                job.message = message
