"""
Dependências de autenticação por tenant.

Uso nas rotas:
    tenant = Depends(get_tenant_by_api_key)   → valida api_key + tenant_id juntos
    tenant = Depends(require_active_tenant)   → igual + garante is_active=True
"""
import secrets
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db


def generate_api_key() -> str:
    """Gera uma chave única segura: 'sk_' + 48 chars urlsafe."""
    return f"sk_{secrets.token_urlsafe(36)}"


def get_tenant_by_api_key(
    tenant_id: str = Query(..., description="ID da clínica"),
    api_key: str = Query(..., description="Chave de API da clínica"),
    db: Session = Depends(get_db),
):
    """
    Valida que a api_key pertence exatamente ao tenant_id informado.
    Impede que uma clínica acesse dados de outra passando tenant_id diferente.
    """
    from app.models.tenant import Tenant

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(404, "Clínica não encontrada")

    if not tenant.api_key:
        raise HTTPException(403, "Esta clínica não possui api_key configurada. Contate o administrador.")

    if tenant.api_key != api_key:
        raise HTTPException(403, "api_key inválida para este tenant_id")

    return tenant


def require_active_tenant(tenant=Depends(get_tenant_by_api_key)):
    """Igual ao anterior, mas garante que a clínica está ativa."""
    if not tenant.is_active:
        raise HTTPException(403, "Clínica desativada")
    return tenant