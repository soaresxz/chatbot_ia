from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import os

from app.core.database import create_tables
from app.core.websocket_manager import active_connections

# ── Routers existentes ───────────────────────────────────────
from app.api.v1.webhook import router as webhook_router
from app.api.v1.send_message import router as send_router
from app.api.v1.human_send import router as human_send_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.routers.dashboard import router as dashboard_router
from app.api.v1.reports import router as reports_router
from app.api.v1.auth import router as auth_router

# ── Novos routers ────────────────────────────────────────────
from app.api.v1.admin import router as admin_router           # /admin/...
from app.api.v1.patients import router as patients_router     # /clinica/.../pacientes
from app.api.v1.assume_release import router as assume_release_router  # /api/v1/conversations/...

# ── Validação obrigatória de env ─────────────────────────────
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
if not ADMIN_API_KEY:
    raise RuntimeError("ADMIN_API_KEY não configurada no Railway!")

# ── App ──────────────────────────────────────────────────────
app = FastAPI(
    title="OdontoIA SaaS",
    description="Plataforma multi-clínica de chatbot WhatsApp para odontologia",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimpleRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        print(f"[REQUEST] {request.method} {request.url.path}")
        response = await call_next(request)
        print(f"[RESPONSE] {response.status_code} {request.url.path}")
        return response


app.add_middleware(SimpleRequestMiddleware)

# ── Routers ──────────────────────────────────────────────────
# Routers COM prefixo /api/v1
app.include_router(webhook_router,           prefix="/api/v1")
app.include_router(send_router,              prefix="/api")
app.include_router(human_send_router,        prefix="/api")
app.include_router(conversations_router,     prefix="/api/v1")
app.include_router(auth_router,              prefix="/api/v1")
app.include_router(assume_release_router,    prefix="/api/v1")  # /api/v1/conversations/assume|release

# Routers SEM prefixo adicional (paths já definidos nos routers)
app.include_router(dashboard_router)    # /dashboard/clinica/{id}
app.include_router(reports_router)      # /reports/...
app.include_router(admin_router)        # /admin/tenants, /admin/create-tenant
app.include_router(patients_router)     # /clinica/{id}/pacientes

# ── WebSocket com keepalive ───────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    print(f"🔌 WebSocket conectado. Total: {len(active_connections)}")

    async def keepalive():
        while True:
            await asyncio.sleep(25)
            try:
                await websocket.send_json({"type": "ping"})
            except Exception:
                break

    ping_task = asyncio.create_task(keepalive())

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ping_task.cancel()
        active_connections.discard(websocket)
        print(f"🔌 WebSocket desconectado. Total: {len(active_connections)}")

# ── Startup ───────────────────────────────────────────────────
@app.on_event("startup")
def startup_event():
    create_tables()
    print("🚀 OdontoIA SaaS iniciado com sucesso!")

# ── Root ──────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "online", "version": "1.0", "saas": "multi-clínica"}