# Receipt OCR Annotator

Tool for experts to review OCR output from receipt images and record feedback. Built with FastHTML + MonsterUI for the UI and Docling for open-source OCR.

## Local Development

1. Install [uv](https://github.com/astral-sh/uv) if you haven’t already.
2. Sync dependencies and create the virtual env:
   ```bash
   uv sync
   ```
3. Run the FastHTML server:
   ```bash
   uv run uvicorn app:app --reload
   ```

Uploads and saved feedback are stored under `static/uploads` and `static/feedback` respectively.

## Deploying to Render

1. Push this repo to your Git hosting provider.
2. In Render, create a **Blueprint** and point it to the repo. The included `render.yaml` describes the service.
3. Set environment variable `PYTHON_VERSION=3.12.7`.
4. (Optional) Add a persistent disk mounted at `/opt/render/project/src/static/feedback` (and `/static/uploads`) to keep saved data across deploys.
5. Deploy. Render will run `uv sync --frozen` during build and `uv run uvicorn app:app --host 0.0.0.0 --port $PORT` to start the service.


