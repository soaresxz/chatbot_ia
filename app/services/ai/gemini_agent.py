import google.generativeai as genai
from datetime import datetime
from sqlalchemy.orm import Session

from app.utils.prompts import ODONTO_PROMPT
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.service import Service
from app.models.message_log import MessageLog

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# ✅ Dicionário em memória removido

HISTORY_LIMIT = 10  # últimas N mensagens carregadas do banco


async def get_services_list(tenant_id: str) -> str:
    db = SessionLocal()
    try:
        services = db.query(Service).filter(
            Service.tenant_id == tenant_id,
            Service.is_active == True
        ).all()
    finally:
        db.close()

    if not services:
        return "Serviços sob consulta (vamos avaliar seu caso)."

    lines = []
    for s in services:
        lines.append(f"- {s.name}: a partir de R$ {float(s.price_from):,.2f}".replace(",", "."))
    return "\n".join(lines)


def load_history(db: Session, tenant_id: str, phone: str) -> list[str]:
    """
    Carrega as últimas HISTORY_LIMIT mensagens da conversa do banco.
    Mensagens 'in' → "Paciente: ..."
    Mensagens 'out' → "Luna: ..."
    """
    messages = (
        db.query(MessageLog)
        .filter(
            MessageLog.tenant_id == tenant_id,
            (MessageLog.from_phone == phone) | (MessageLog.to_phone == phone),
        )
        .order_by(MessageLog.created_at.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )

    # Reverte para ordem cronológica
    messages = list(reversed(messages))

    history = []
    for m in messages:
        if m.direction == "in":
            history.append(f"Paciente: {m.message}")
        else:
            history.append(f"Luna: {m.message}")
    return history


async def get_ai_response(message: str, tenant, phone: str) -> str:
    db = SessionLocal()
    try:
        # ✅ Carrega histórico do banco — persiste entre deploys e crashes
        history = load_history(db, tenant.id, phone)
    finally:
        db.close()

    # Adiciona a mensagem atual ao histórico (ainda não está no banco neste momento)
    history.append(f"Paciente: {message}")
    if len(history) > HISTORY_LIMIT:
        history = history[-HISTORY_LIMIT:]

    history_text = "\n".join(history)
    services_text = await get_services_list(tenant.id)

    prompt = ODONTO_PROMPT.format(
        clinic_name=tenant.name,
        dentist_name=getattr(tenant, 'dentist_name', ''),
        services_list=services_text,
        today=datetime.now().strftime('%d/%m/%Y')
    )

    full_prompt = f"{prompt}\n\nHistórico:\n{history_text}\n\nResponda direto:"

    response = model.generate_content(full_prompt)
    ai_text = response.text.strip()

    return ai_text