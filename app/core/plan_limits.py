"""
Limites e validações por plano.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

PLAN_LIMITS = {
    "basic":      3_000,
    "pro":        40,
    "enterprise": None,   # ilimitado
}

# Mensagem enviada ao paciente quando o limite é atingido
LIMIT_REACHED_MESSAGE = (
    "Olá! Nossa clínica está temporariamente indisponível pelo chat. "
    "Por favor, entre em contato por outro canal. Obrigado! 🙏"
)


def get_monthly_message_count(db: Session, tenant_id: str) -> int:
    """Conta mensagens de saída do bot no mês atual."""
    from app.models.message_log import MessageLog

    inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return db.scalar(
        select(func.count()).where(
            and_(
                MessageLog.tenant_id == tenant_id,
                MessageLog.direction == "out",
                MessageLog.created_at >= inicio_mes,
            )
        )
    ) or 0


def check_plan_limit(db: Session, tenant) -> tuple[bool, str | None]:
    """
    Verifica se o tenant ainda tem cota de mensagens.

    Retorna:
        (True, None)         → dentro do limite, pode responder
        (False, motivo)      → limite atingido
    """
    limit = PLAN_LIMITS.get(tenant.plan or "basic")

    if limit is None:
        return True, None  # enterprise — ilimitado

    count = get_monthly_message_count(db, tenant.id)

    if count >= limit:
        return False, (
            f"Limite do plano {tenant.plan} atingido "
            f"({count}/{limit} mensagens este mês)"
        )

    return True, None