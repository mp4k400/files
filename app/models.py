from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class ModelMetadata(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class JobCreateRequest(BaseModel):
    model_id: str
    prompt: str
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    steps: Optional[int] = None
    guidance_scale: Optional[float] = None
    seed: Optional[int] = None
    resolution: Optional[str] = None
    aspect_ratio: Optional[str] = None
    strength: Optional[float] = None
    duration: Optional[float] = None
    batch_count: Optional[int] = None
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class JobRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    model_id: str
    prompt: str
    status: JobStatus = JobStatus.queued
    progress: float = 0.0
    message: Optional[str] = None
    created_at: float
    updated_at: float
    input_files: Dict[str, Optional[str]] = Field(default_factory=dict)
    output_files: List[str] = Field(default_factory=list)
    metadata_path: Optional[str] = None
    remote_job_id: Optional[str] = None
    extra_params: Dict[str, Any] = Field(default_factory=dict)
