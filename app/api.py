from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .jobs import JobManager
from .models import JobCreateRequest, JobRecord
from .wavespeed import WaveSpeedClient, WaveSpeedError

router = APIRouter()
manager = JobManager()
client = WaveSpeedClient()


@router.get("/models")
def list_models() -> list[dict]:
    try:
        return client.list_models()
    except WaveSpeedError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/jobs", response_model=JobRecord)
def create_job(request: JobCreateRequest) -> JobRecord:
    if not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    job = manager.submit(request)
    return job


@router.get("/jobs/{job_id}", response_model=JobRecord)
def get_job(job_id: str) -> JobRecord:
    job = manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
