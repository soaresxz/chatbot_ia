"""
Rotas administrativas — apenas super_admin.

Paths gerados (sem prefixo adicional no include_router):
  GET  /admin/tenants           → lista clínicas (usado pelo frontend)
  GET  /admin/create-tenant     → cria clínica via query params (compatibilidade frontend)
  POST /admin/tenants           → cria clínica via JSON body (Swagger / novos clientes)
  PATCH /admin/tenants/{id}/plan → altera plano
  POST /admin/change-plan       → altera plano via query params (legado)
"""
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


# ── helpers ──────────────────────────────────────────────────

def slugify(text: str) -> str:
    replacements = str.maketrans("ãâáàäçéêèëíîìïóôòöúûùüñ", "aaaaceeeeiiiiooooouuuun")
    return re.sub(r"[^a-z0-9_]", "_", text.lower().translate(replacements)).strip("_")


def _build_tenant(db, name, dentist_name, whatsapp_number, plan):
    from app.models.tenant import Tenant

    if db.query(Tenant).filter(Tenant.whatsapp_number == whatsapp_number).first():
        raise HTTPException(400, "Número de WhatsApp já cadastrado")

    tenant_id = f"clinica_{slugify(name)}"
    if db.query(Tenant).filter(Tenant.id == tenant_id).first():
        raise HTTPException(400, f"Já existe uma clínica com o ID '{tenant_id}'. Use um nome diferente.")

    t = Tenant(
        id=tenant_id,
        name=name,
        dentist_name=dentist_name,
        whatsapp_number=whatsapp_number,
        plan=plan,
        is_active=True,
        human_mode_active=False,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


# ── listar clínicas ───────────────────────────────────────────

@router.get("/tenants")
def list_tenants(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.models.tenant import Tenant

    tenants = db.query(Tenant).all()
    return {
        "total": len(tenants),
        "tenants": [
            {
                "id": t.id,
                "name": t.name,
                "dentist_name": t.dentist_name,
                "whatsapp_number": t.whatsapp_number,
                "plan": t.plan,
                "is_active": t.is_active,
            }
            for t in tenants
        ],
    }


# ── criar clínica — GET com query params (compatibilidade frontend) ──

@router.get("/create-tenant", summary="Criar clínica (frontend legado)")
def create_tenant_get(
    name: str = Query(...),
    dentist_name: str = Query(...),
    whatsapp_number: str = Query(...),
    plan: str = Query("basic"),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    t = _build_tenant(db, name, dentist_name, whatsapp_number, plan)
    return {"status": "success", "tenant_id": t.id, "name": t.name}


# ── criar clínica — POST com JSON body (Swagger / API) ───────

class CreateTenantRequest(BaseModel):
    name: str
    dentist_name: str
    whatsapp_number: str
    plan: str = "basic"


@router.post("/tenants", status_code=201, summary="Criar clínica (JSON body)")
def create_tenant_post(
    data: CreateTenantRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    t = _build_tenant(db, data.name, data.dentist_name, data.whatsapp_number, data.plan)
    return {
        "status": "success",
        "tenant_id": t.id,
        "name": t.name,
        "dentist_name": t.dentist_name,
        "whatsapp_number": t.whatsapp_number,
        "plan": t.plan,
    }


# ── alterar plano — PATCH JSON (novo) ────────────────────────

class UpdatePlanRequest(BaseModel):
    plan: str


@router.patch("/tenants/{tenant_id}/plan")
def change_plan_patch(
    tenant_id: str,
    data: UpdatePlanRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.models.tenant import Tenant

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(404, "Clínica não encontrada")
    tenant.plan = data.plan
    db.commit()
    db.refresh(tenant)
    return {"status": "success", "tenant_id": tenant.id, "novo_plano": tenant.plan}


# ── alterar plano — POST query params (legado) ───────────────

@router.post("/change-plan", summary="Alterar plano (query params, legado)")
def change_plan_post(
    tenant_id: str = Query(...),
    new_plan: str = Query(...),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.models.tenant import Tenant

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(404, "Clínica não encontrada")
    tenant.plan = new_plan
    db.commit()
    db.refresh(tenant)
    return {
        "status": "success",
        "mensagem": f"Plano de '{tenant.name}' alterado para {new_plan}",
        "tenant_id": tenant.id,
        "novo_plano": tenant.plan,
    }


# ── desativar clínica ─────────────────────────────────────────

@router.delete("/tenants/{tenant_id}")
def deactivate_tenant(
    tenant_id: str,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.models.tenant import Tenant

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(404, "Clínica não encontrada")
    tenant.is_active = False
    db.commit()
    return {"status": "success", "message": f"Clínica '{tenant.name}' desativada."}