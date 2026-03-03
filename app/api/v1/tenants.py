from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.auth import require_admin

router = APIRouter(prefix="/admin/tenants", tags=["admin - tenants"])


class CreateTenantRequest(BaseModel):
    name: str
    dentist_name: str
    whatsapp_number: str
    plan: str = "basic"


class UpdatePlanRequest(BaseModel):
    plan: str


@router.post("", status_code=201)
def create_tenant(
    data: CreateTenantRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Cria uma nova clínica. Apenas super_admin."""
    from app.models.tenant import Tenant

    if db.query(Tenant).filter(Tenant.whatsapp_number == data.whatsapp_number).first():
        raise HTTPException(400, "Número de WhatsApp já cadastrado")

    tenant_id = (
        "clinica_"
        + data.name.lower()
        .replace(" ", "_")
        .replace("ã", "a")
        .replace("ç", "c")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("á", "a")
        .replace("â", "a")
        .replace("í", "i")
        .replace("ú", "u")
    )

    # Garante ID único caso já exista uma clínica com nome similar
    if db.query(Tenant).filter(Tenant.id == tenant_id).first():
        raise HTTPException(400, f"Já existe uma clínica com o ID '{tenant_id}'. Escolha um nome diferente.")

    new_tenant = Tenant(
        id=tenant_id,
        name=data.name,
        dentist_name=data.dentist_name,
        whatsapp_number=data.whatsapp_number,
        plan=data.plan,
        is_active=True,
        human_mode_active=False,
    )
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    return {
        "status": "success",
        "tenant_id": new_tenant.id,
        "name": new_tenant.name,
        "dentist_name": new_tenant.dentist_name,
        "whatsapp_number": new_tenant.whatsapp_number,
        "plan": new_tenant.plan,
    }


@router.get("")
def list_tenants(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lista todas as clínicas. Apenas super_admin."""
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


@router.patch("/{tenant_id}/plan")
def change_plan(
    tenant_id: str,
    data: UpdatePlanRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Altera o plano de uma clínica. Apenas super_admin."""
    from app.models.tenant import Tenant

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(404, "Clínica não encontrada")

    tenant.plan = data.plan
    db.commit()
    db.refresh(tenant)

    return {
        "status": "success",
        "tenant_id": tenant.id,
        "name": tenant.name,
        "novo_plano": tenant.plan,
    }


@router.delete("/{tenant_id}")
def deactivate_tenant(
    tenant_id: str,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Desativa uma clínica (soft delete). Apenas super_admin."""
    from app.models.tenant import Tenant

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(404, "Clínica não encontrada")

    tenant.is_active = False
    db.commit()

    return {"status": "success", "message": f"Clínica '{tenant.name}' desativada."}