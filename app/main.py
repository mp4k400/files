from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import gradio as gr

from .api import router
from .config import settings
from .storage import ensure_dirs
from .ui import create_ui


def create_app() -> FastAPI:
    ensure_dirs()
    app = FastAPI(title="WaveSpeedAI Local Runner")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")
    app.mount("/data", StaticFiles(directory=settings.data_dir), name="data")
    ui = create_ui()
    app = gr.mount_gradio_app(app, ui, path="/")
    return app


app = create_app()
