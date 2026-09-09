import sys
import os
import uuid
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

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
            response.set_cookie(key="session_id", value=session_id, httponly=True, samesite='lax')
            
        return response

app.add_middleware(SessionMiddleware)

app.include_router(api_router, prefix="/api")

# Serve the UI static files
app.mount("/ui", StaticFiles(directory=os.path.join(BASE_DIR, "app", "ui")), name="ui")

# Serve the exports directory for downloads
exports_dir = os.path.join(BASE_DIR, "exports")
os.makedirs(exports_dir, exist_ok=True)
app.mount("/exports", StaticFiles(directory=exports_dir), name="exports")

@app.get("/")
def read_root():
    return RedirectResponse(url="/ui/login.html")

if __name__ == "__main__":
    print("Starting Analise de Compras Server on http://0.0.0.0:8686")
    uvicorn.run("main:app", host="0.0.0.0", port=8686, reload=True)
