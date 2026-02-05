# WaveSpeedAI Local Runner

A production-ready local web application for running **WaveSpeedAI paid models** with local image and video uploads. Built with **FastAPI** (backend API + job queue) and **Gradio** (UI) and designed for local or RunPod deployments.

## Features
- ✅ Dynamic WaveSpeedAI model list and per-model input capabilities
- ✅ Local image & video uploads
- ✅ Advanced settings (steps, CFG, seed, resolution, strength, duration, batch count)
- ✅ Async job queue and status polling
- ✅ Output gallery with image previews, video playback, and downloads
- ✅ Local storage of inputs, outputs, and metadata for reproducibility

## Requirements
- Python 3.10+
- WaveSpeedAI API key

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run locally
```bash
export WAVESPEED_API_KEY="your_api_key_here"
uvicorn app.main:app --host 0.0.0.0 --port 7860
```

Open <http://localhost:7860>.

## Run on RunPod
Expose port `7860` and set environment variables:
- `WAVESPEED_API_KEY`
- `WAVESPEED_BASE_URL` (optional, defaults to https://api.wavespeed.ai/v1)
- `WAVESPEED_DATA_DIR` (optional, defaults to ./data)

## Data Storage
All runs are persisted to the `data/` directory:
- `data/inputs/` uploaded input files
- `data/outputs/` generated outputs
- `data/metadata/` JSON metadata for reproducible runs

## API Endpoints
The FastAPI backend is available under `/api`:
- `GET /api/models` - list WaveSpeedAI models
- `POST /api/jobs` - create a job
- `GET /api/jobs/{job_id}` - job status and metadata

## Notes on WaveSpeedAI API
This application assumes the WaveSpeedAI API uses:
- Bearer token authentication
- `GET /models` for model listing
- `POST /files` for file uploads
- `POST /generate/{model_id}` for async generation
- `GET /jobs/{job_id}` for job status

If WaveSpeedAI endpoints differ, adjust `app/wavespeed.py`.
