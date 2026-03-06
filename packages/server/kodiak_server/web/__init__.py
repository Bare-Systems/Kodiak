"""Kodiak Web UI (stub).

Serves a minimal status dashboard. Will be replaced with
a full SPA when the web UI becomes a priority.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATE_DIR = Path(__file__).parent / "templates"


def create_web_app() -> FastAPI:
    """Create the web UI application."""
    app = FastAPI()
    templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    return app
