# WaveSpeedAI Jupyter Studio (RunPod)

A Jupyter-native WaveSpeedAI client that runs entirely inside a notebook using **ipywidgets** and **httpx**. The API key is requested at runtime via `getpass()` and stored only in memory.

## Usage
Open `wavespeed_jupyter.ipynb` and run the cells in order. The UI will let you select a model, inspect its `api_schema`, provide inputs, submit jobs asynchronously, and download outputs to `outputs/`.

## Requirements
Installed in notebook Cell 1 (`httpx`, `ipywidgets`).
