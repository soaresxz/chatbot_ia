"""
Limites e permissões por plano.

Planos:
  basic      → 3.000 msg/mês | só chat
  pro        → 10.000 msg/mês | chat + agendamentos + relatórios + IA avançada
  enterprise → ilimitado | todas as features + integrações customizadas
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, select

# ── Limites de mensagens ──────────────────────────────────────────────────────

# PLAN_LIMITS mantido para compatibilidade com dashboard_service.py
PLAN_LIMITS: dict[str, int | None] = {
    "basic": 3_000,
    "pro": 10_000,
    "enterprise": None,   # ilimitado
}

# Alias novo (usado internamente nos arquivos novos)
PLAN_MESSAGE_LIMITS = PLAN_LIMITS

# ── Permissões de features ────────────────────────────────────────────────────

PLAN_SCHEDULING: dict[str, bool] = {
    "basic": False,
    "pro": True,
    "enterprise": True,
}

PLAN_REPORTS: dict[str, bool] = {
    "basic": False,
    "pro": True,
    "enterprise": True,
}

PLAN_CUSTOM_INTEGRATIONS: dict[str, bool] = {
    "basic": False,
    "pro": False,
    "enterprise": True,
}


def has_feature(plan: str, feature: str) -> bool:
    mapping = {
        "scheduling": PLAN_SCHEDULING,
        "reports": PLAN_REPORTS,
        "custom_integrations": PLAN_CUSTOM_INTEGRATIONS,
    }
    return mapping.get(feature, {}).get(plan.lower(), False)


# ── Contagem mensal de mensagens ──────────────────────────────────────────────

def get_monthly_message_count(db: Session, tenant_id: str) -> int:
    """Retorna o total de mensagens enviadas pelo bot no mês atual."""
    from app.models.message_log import MessageLog

    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return db.query(func.count(MessageLog.id)).filter(
        MessageLog.tenant_id == tenant_id,
        MessageLog.created_at >= start_of_month,
        MessageLog.direction == "out",
    ).scalar() or 0


def check_plan_limit(db: Session, tenant_id: str, plan: str) -> tuple[bool, int | None]:
    """
    Verifica se o tenant ainda está dentro do limite mensal.

    Returns:
        (allowed: bool, limit: int | None)
    """
    limit = PLAN_LIMITS.get(plan.lower())
    if limit is None:
        return True, None  # enterprise → ilimitado

    count = get_monthly_message_count(db, tenant_id)
    return count < limit, limit