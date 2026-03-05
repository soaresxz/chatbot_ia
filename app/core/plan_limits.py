"""
Limites e permissões por plano.

Planos:
  basic      → 3.000 msg/mês | só chat
  pro        → 10.000 msg/mês | chat + agendamentos + relatórios + IA avançada
  enterprise → ilimitado | todas as features + integrações customizadas
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# ─────────────────────────────────────────────────────────────────────────────
# Limites de mensagens
# ─────────────────────────────────────────────────────────────────────────────

PLAN_MESSAGE_LIMITS: dict[str, int | None] = {
    "basic": 3_000,
    "pro": 10_000,
    "enterprise": None,   # ilimitado
}

# ─────────────────────────────────────────────────────────────────────────────
# Permissões de features
# ─────────────────────────────────────────────────────────────────────────────

# Agendamento via bot (criar, confirmar, consultar horários)
PLAN_SCHEDULING: dict[str, bool] = {
    "basic": False,
    "pro": True,
    "enterprise": True,
}

# Relatórios avançados
PLAN_REPORTS: dict[str, bool] = {
    "basic": False,
    "pro": True,
    "enterprise": True,
}

# Integrações customizadas
PLAN_CUSTOM_INTEGRATIONS: dict[str, bool] = {
    "basic": False,
    "pro": False,
    "enterprise": True,
}


def has_feature(plan: str, feature: str) -> bool:
    """
    Verifica se o plano possui determinada feature.

    Args:
        plan: "basic" | "pro" | "enterprise"
        feature: "scheduling" | "reports" | "custom_integrations"

    Returns:
        True se o plano tem acesso.
    """
    mapping = {
        "scheduling": PLAN_SCHEDULING,
        "reports": PLAN_REPORTS,
        "custom_integrations": PLAN_CUSTOM_INTEGRATIONS,
    }
    feature_map = mapping.get(feature, {})
    return feature_map.get(plan.lower(), False)


# ─────────────────────────────────────────────────────────────────────────────
# Verificação assíncrona de limite mensal
# ─────────────────────────────────────────────────────────────────────────────

async def check_plan_limit(
    db: AsyncSession, tenant_id: int, plan: str
) -> tuple[bool, int | None]:
    """
    Verifica se o tenant ainda está dentro do limite mensal de mensagens.

    Returns:
        (allowed: bool, limit: int | None)
    """
    limit = PLAN_MESSAGE_LIMITS.get(plan.lower())
    if limit is None:
        return True, None  # enterprise → ilimitado

    from app.models.message_log import MessageLog
    from datetime import datetime

    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(func.count(MessageLog.id)).where(
            MessageLog.tenant_id == tenant_id,
            MessageLog.created_at >= start_of_month,
            MessageLog.direction == "outbound",
        )
    )
    count = result.scalar_one()
    return count < limit, limit