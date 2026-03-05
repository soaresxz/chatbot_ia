"""
Gemini Agent com suporte a function calling para agendamentos.

Fluxo:
1. Recebe mensagem + histórico
2. Envia para Gemini com tools de agendamento (apenas planos Pro/Enterprise)
3. Se Gemini chamar uma tool → executa → devolve resultado ao Gemini
4. Retorna texto final para o paciente

Detecta AGENDAMENTO_PENDENTE no resultado da tool para acionar fluxo SIM/NÃO.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.appointment_tools import APPOINTMENT_TOOLS, execute_tool

logger = logging.getLogger(__name__)

# Configuração da API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))

SYSTEM_PROMPT = """Você é a assistente virtual de uma clínica odontológica. 
Seja sempre cordial, objetiva e profissional.

Para agendamentos:
- Quando o paciente quiser marcar uma consulta, use a ferramenta verificar_disponibilidade para mostrar os horários disponíveis.
- Depois que o paciente escolher o horário, use criar_agendamento e peça confirmação: "Para confirmar seu agendamento, responda SIM. Para cancelar, responda NÃO."
- Quando o paciente perguntar sobre seus agendamentos, use listar_agendamentos_paciente.

Sempre confirme as informações antes de criar o agendamento.
"""


def _build_gemini_tools(has_scheduling: bool) -> Optional[list]:
    """Retorna as tools do Gemini apenas se o plano permite agendamentos."""
    if not has_scheduling:
        return None
    return [{"function_declarations": APPOINTMENT_TOOLS}]


async def generate_response(
    message: str,
    history: list[dict],
    db: AsyncSession,
    tenant_id: int,
    patient_phone: str,
    has_scheduling: bool = False,       # True para Pro/Enterprise
    tenant_context: str = "",           # Ex: "Clínica Sorriso | Dr. João"
) -> tuple[str, Optional[dict]]:
    """
    Gera resposta do Gemini.

    Retorna:
        (texto_resposta, pending_appointment_info | None)

    pending_appointment_info é dict {id, data, hora, procedimento} quando
    um agendamento pendente foi criado e aguarda confirmação SIM/NÃO.
    """
    system = SYSTEM_PROMPT
    if tenant_context:
        system = f"Contexto da clínica: {tenant_context}\n\n" + system

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system,
        tools=_build_gemini_tools(has_scheduling),
    )

    # Monta histórico no formato Gemini
    chat_history = []
    for msg in history:
        role = "user" if msg.get("role") == "user" else "model"
        chat_history.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

    chat = model.start_chat(history=chat_history)

    # Primeira resposta
    response = await _send_async(chat, message)
    pending_info = None

    # Loop de function calling (máximo 3 iterações para evitar loop infinito)
    for _ in range(3):
        tool_calls = _extract_tool_calls(response)
        if not tool_calls:
            break

        tool_results = []
        for call in tool_calls:
            tool_result = await execute_tool(
                tool_name=call["name"],
                args=call["args"],
                db=db,
                tenant_id=tenant_id,
                patient_phone=patient_phone,
            )
            logger.info(f"[tool={call['name']}] result: {tool_result[:120]}")

            # Detecta agendamento pendente
            if tool_result.startswith("AGENDAMENTO_PENDENTE|"):
                pending_info = _parse_pending_info(tool_result)

            tool_results.append(
                {
                    "function_response": {
                        "name": call["name"],
                        "response": {"result": tool_result},
                    }
                }
            )

        response = await _send_tool_results_async(chat, tool_results)

    text = _extract_text(response)
    return text, pending_info


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

async def _send_async(chat, message: str):
    """Wrapper assíncrono para chat.send_message (SDK síncrono)."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, chat.send_message, message)


async def _send_tool_results_async(chat, tool_results: list):
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, chat.send_message, tool_results)


def _extract_tool_calls(response) -> list[dict]:
    calls = []
    try:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                calls.append({
                    "name": part.function_call.name,
                    "args": dict(part.function_call.args),
                })
    except (AttributeError, IndexError):
        pass
    return calls


def _extract_text(response) -> str:
    try:
        return response.text
    except Exception:
        try:
            parts = response.candidates[0].content.parts
            return " ".join(p.text for p in parts if hasattr(p, "text") and p.text)
        except Exception:
            return "Desculpe, não consegui processar sua mensagem."


def _parse_pending_info(raw: str) -> dict:
    """
    Extrai dados do token AGENDAMENTO_PENDENTE|id=X|data=...|hora=...|procedimento=...
    """
    info = {}
    for part in raw.split("|")[1:]:
        k, _, v = part.partition("=")
        info[k.strip()] = v.strip()
    return info