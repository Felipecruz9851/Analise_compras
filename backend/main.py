import sys
import os
import uuid
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import settings
from app.api import router as api_router
from app.context import session_id_var

app = FastAPI()


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get("session_id")
        is_new_session = False

        if not session_id:
            session_id = str(uuid.uuid4())
            is_new_session = True

        session_id_var.set(session_id)

        response = await call_next(request)

        if is_new_session:
            response.set_cookie(
                key="session_id", value=session_id, httponly=True, samesite="lax"
            )

        return response


app.add_middleware(SessionMiddleware)

# API routes
app.include_router(api_router, prefix="/api")

# Serve the exports directory for downloads
app.mount("/exports", StaticFiles(directory=str(settings.EXPORTS_DIR)), name="exports")

# Serve the CSV directory for downloads
app.mount("/csv_files", StaticFiles(directory=str(settings.CSV_DIR)), name="csv_files")

# Serve the legacy UI static files
ui_dir = os.path.join(BASE_DIR, "app", "ui")
if os.path.exists(ui_dir):
    app.mount("/ui", StaticFiles(directory=ui_dir), name="ui")

# Serve the React frontend (check frontend/dist, fallback to backend/dist)
frontend_dist = os.environ.get(
    "FRONTEND_DIST",
    os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "dist")),
)
if not os.path.exists(frontend_dist):
    frontend_dist = os.path.join(BASE_DIR, "dist")

dist_dir = frontend_dist
dist_assets = os.path.join(dist_dir, "assets")
if os.path.exists(dist_assets):
    app.mount("/assets", StaticFiles(directory=dist_assets), name="react_assets")


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    file_path = os.path.join(dist_dir, full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)

    index_path = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return RedirectResponse(url="/ui/login.html")


if __name__ == "__main__":
    print("Starting Analise de Compras Server on http://0.0.0.0:8686")
    uvicorn.run("main:app", host="0.0.0.0", port=8686, reload=True)
