# P9.T1 — FastAPI app scaffold, bind 127.0.0.1 by default
from __future__ import annotations

import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


def create_application() -> FastAPI:
    app = FastAPI(title="LLM Research Harness UI", docs_url="/api/docs")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    from harness.ui.routes_endpoints import mount as _mount_endpoints
    from harness.ui.routes_keys import mount as _mount_keys
    from harness.ui.routes_chat import mount as _mount_chat
    from harness.ui.routes_logs import mount as _mount_logs
    from harness.ui.routes_config import mount as _mount_config
    _mount_endpoints(app)
    _mount_keys(app)
    _mount_chat(app)
    _mount_logs(app)
    _mount_config(app)

    return app


def launch() -> None:
    """Console script entry point for `harness-ui`."""
    import uvicorn
    uvicorn.run(create_application(), host="127.0.0.1", port=8080)
