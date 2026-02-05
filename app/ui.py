from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import gradio as gr

from .api import manager
from .models import JobCreateRequest, JobStatus
from .wavespeed import WaveSpeedClient, WaveSpeedError


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv"}


def _model_capabilities(model: Dict[str, Any]) -> Dict[str, bool]:
    capabilities = model.get("capabilities", {}) if model else {}
    schema = model.get("input_schema", {}) if model else {}
    fields = schema.get("properties", schema)
    return {
        "image": capabilities.get("image", "image" in fields),
        "video": capabilities.get("video", "video" in fields),
        "strength": capabilities.get("strength", "strength" in fields),
        "duration": capabilities.get("duration", "duration" in fields),
        "steps": capabilities.get("steps", "steps" in fields),
        "guidance_scale": capabilities.get("guidance_scale", "guidance_scale" in fields),
        "resolution": capabilities.get("resolution", "resolution" in fields),
        "aspect_ratio": capabilities.get("aspect_ratio", "aspect_ratio" in fields),
        "seed": capabilities.get("seed", "seed" in fields),
        "batch_count": capabilities.get("batch_count", "batch_count" in fields),
    }


def _load_models() -> Tuple[List[str], Dict[str, Dict[str, Any]], str]:
    client = WaveSpeedClient()
    try:
        models = client.list_models()
    except WaveSpeedError as exc:
        return [], {}, f"❌ Failed to load models: {exc}"
    model_map = {model["id"]: model for model in models if "id" in model}
    choices = [f"{model['id']} - {model.get('name', model['id'])}" for model in models]
    return choices, model_map, "✅ Models loaded."


def _parse_extra(extra_text: str) -> Dict[str, Any]:
    if not extra_text:
        return {}
    return json.loads(extra_text)


def _submit_job(
    model_choice: str,
    prompt: str,
    image_path: str | None,
    video_path: str | None,
    steps: int | None,
    guidance_scale: float | None,
    seed: int | None,
    resolution: str | None,
    aspect_ratio: str | None,
    strength: float | None,
    duration: float | None,
    batch_count: int | None,
    extra_text: str,
    model_map: Dict[str, Dict[str, Any]],
) -> Tuple[str, str]:
    model_id = model_choice.split(" - ")[0]
    if model_id not in model_map:
        return "", "❌ Please select a model."
    try:
        extra_params = _parse_extra(extra_text)
    except json.JSONDecodeError as exc:
        return "", f"❌ Invalid JSON in extra parameters: {exc}"
    if steps is not None:
        extra_params["steps"] = steps
    if guidance_scale is not None:
        extra_params["guidance_scale"] = guidance_scale
    if seed is not None:
        extra_params["seed"] = seed
    if resolution:
        extra_params["resolution"] = resolution
    if aspect_ratio:
        extra_params["aspect_ratio"] = aspect_ratio
    if strength is not None:
        extra_params["strength"] = strength
    if duration is not None:
        extra_params["duration"] = duration
    if batch_count is not None:
        extra_params["batch_count"] = batch_count
    request = JobCreateRequest(
        model_id=model_id,
        prompt=prompt,
        image_path=image_path,
        video_path=video_path,
        steps=steps,
        guidance_scale=guidance_scale,
        seed=seed,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        strength=strength,
        duration=duration,
        batch_count=batch_count,
        extra_params=extra_params,
    )
    job = manager.submit(request)
    return job.id, f"✅ Job {job.id} queued."


def _poll_job(job_id: str) -> Tuple[str, float, List[str], List[str]]:
    if not job_id:
        return "", 0.0, [], []
    job = manager.get(job_id)
    if not job:
        return "❌ Job not found.", 0.0, [], []
    status = f"Status: {job.status.value}"
    if job.message:
        status += f" | {job.message}"
    image_outputs: List[str] = []
    video_outputs: List[str] = []
    if job.status == JobStatus.succeeded:
        for path in job.output_files:
            ext = path.lower()
            if any(ext.endswith(suffix) for suffix in IMAGE_EXTENSIONS):
                image_outputs.append(path)
            elif any(ext.endswith(suffix) for suffix in VIDEO_EXTENSIONS):
                video_outputs.append(path)
    return status, job.progress, image_outputs, video_outputs


def _update_visibility(model_choice: str, model_map: Dict[str, Dict[str, Any]]):
    model_id = model_choice.split(" - ")[0] if model_choice else ""
    model = model_map.get(model_id, {})
    caps = _model_capabilities(model)
    description = model.get("description", "")
    return (
        gr.update(visible=caps["image"]),
        gr.update(visible=caps["video"]),
        gr.update(visible=caps["steps"]),
        gr.update(visible=caps["guidance_scale"]),
        gr.update(visible=caps["seed"]),
        gr.update(visible=caps["resolution"]),
        gr.update(visible=caps["aspect_ratio"]),
        gr.update(visible=caps["strength"]),
        gr.update(visible=caps["duration"]),
        gr.update(visible=caps["batch_count"]),
        gr.update(value=description or "No description available."),
    )


def create_ui() -> gr.Blocks:
    with gr.Blocks(title="WaveSpeedAI Local Runner", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            "# WaveSpeedAI Local Runner\n"
            "Run WaveSpeedAI paid models locally with queued jobs, rich settings, and file uploads."
        )
        status_banner = gr.Markdown("Loading models...")
        model_map_state = gr.State({})
        job_id_state = gr.State("")

        with gr.Row():
            model_dropdown = gr.Dropdown(label="Model", choices=[])
            refresh_models = gr.Button("Refresh Models")

        model_description = gr.Markdown("")

        with gr.Row():
            prompt = gr.Textbox(lines=3, label="Prompt")

        with gr.Row():
            image_upload = gr.File(label="Image Upload", file_types=["image"], type="filepath")
            video_upload = gr.File(label="Video Upload", file_types=["video"], type="filepath")

        with gr.Accordion("Advanced Settings", open=False):
            with gr.Row():
                steps = gr.Number(label="Steps", precision=0)
                guidance_scale = gr.Number(label="CFG / Guidance Scale", precision=2)
                seed = gr.Number(label="Seed", precision=0)
            with gr.Row():
                resolution = gr.Textbox(label="Resolution (e.g. 1024x1024)")
                aspect_ratio = gr.Textbox(label="Aspect Ratio (e.g. 16:9)")
            with gr.Row():
                strength = gr.Slider(0, 1, label="Strength", step=0.05)
                duration = gr.Number(label="Duration (seconds)", precision=2)
                batch_count = gr.Number(label="Batch Count", precision=0)
            extra_params = gr.Code(
                label="Extra Parameters (JSON)", language="json", lines=6
            )

        submit = gr.Button("Queue Job", variant="primary")
        job_status = gr.Markdown("Awaiting submission.")
        progress = gr.Slider(0, 1, value=0, label="Progress", interactive=False)

        with gr.Row():
            gallery = gr.Gallery(label="Image Outputs", columns=3, height=300)
            video_outputs = gr.Video(label="Video Output")

        downloads = gr.File(label="Downloads")

        def load_models():
            choices, model_map, message = _load_models()
            default_choice = choices[0] if choices else None
            return gr.update(choices=choices, value=default_choice), model_map, message

        demo.load(load_models, outputs=[model_dropdown, model_map_state, status_banner])
        refresh_models.click(
            load_models, outputs=[model_dropdown, model_map_state, status_banner]
        )

        model_dropdown.change(
            _update_visibility,
            inputs=[model_dropdown, model_map_state],
            outputs=[
                image_upload,
                video_upload,
                steps,
                guidance_scale,
                seed,
                resolution,
                aspect_ratio,
                strength,
                duration,
                batch_count,
                model_description,
            ],
        )

        submit.click(
            _submit_job,
            inputs=[
                model_dropdown,
                prompt,
                image_upload,
                video_upload,
                steps,
                guidance_scale,
                seed,
                resolution,
                aspect_ratio,
                strength,
                duration,
                batch_count,
                extra_params,
                model_map_state,
            ],
            outputs=[job_id_state, job_status],
        )

        def update_outputs(job_id: str):
            status, prog, images, videos = _poll_job(job_id)
            video_path = videos[0] if videos else None
            return status, prog, images, video_path, images + videos

        timer = gr.Timer(3)
        timer.tick(
            update_outputs,
            inputs=[job_id_state],
            outputs=[job_status, progress, gallery, video_outputs, downloads],
        )

    return demo
