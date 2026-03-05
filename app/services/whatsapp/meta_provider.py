"""
WhatsApp Business Cloud API (Meta) provider.
Documentação: https://developers.facebook.com/docs/whatsapp/cloud-api
"""
import httpx
from app.services.whatsapp.provider import WhatsAppProvider


class MetaProvider(WhatsAppProvider):
    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, phone_number_id: str, access_token: str):
        """
        phone_number_id: ID do número no Meta Business
                         (encontrado em WhatsApp > Getting Started no painel)
        access_token:    Token de acesso permanente gerado no Meta Business
        """
        self.phone_number_id = phone_number_id
        self.access_token = access_token

    async def send_message(self, to: str, body: str) -> str:
        """Envia mensagem de texto simples via Cloud API."""
        to_clean = to.replace("whatsapp:", "").replace("+", "").strip()
        if not to_clean.startswith("+"):
            to_clean = f"+{to_clean}"

        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_clean,
            "type": "text",
            "text": {"body": body},
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            # Retorna o message_id da Meta (equivalente ao SID do Twilio)
            return data.get("messages", [{}])[0].get("id", "")

    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "pt_BR",
        components: list = None,
    ) -> str:
        """
        Envia mensagem usando template aprovado pela Meta.
        Necessário para iniciar conversa (fora da janela de 24h).

        Exemplo de uso:
            await provider.send_template(
                to="+5511999999999",
                template_name="confirmacao_agendamento",
                components=[{
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": "Dr. João"},
                        {"type": "text", "text": "15/03 às 10h"},
                    ]
                }]
            )
        """
        to_clean = to.replace("whatsapp:", "").replace("+", "").strip()
        if not to_clean.startswith("+"):
            to_clean = f"+{to_clean}"

        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_clean,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or [],
            },
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            return data.get("messages", [{}])[0].get("id", "")

    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: list[dict],
    ) -> str:
        """
        Envia mensagem com botões interativos.
        Máximo de 3 botões.

        Exemplo:
            await provider.send_interactive_buttons(
                to="+5511999999999",
                body_text="Confirmar agendamento para 15/03 às 10h?",
                buttons=[
                    {"id": "confirm", "title": "✅ Confirmar"},
                    {"id": "cancel",  "title": "❌ Cancelar"},
                ]
            )
        """
        to_clean = to.replace("whatsapp:", "").replace("+", "").strip()
        if not to_clean.startswith("+"):
            to_clean = f"+{to_clean}"

        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_clean,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": btn["id"], "title": btn["title"]},
                        }
                        for btn in buttons[:3]  # Meta limita a 3 botões
                    ]
                },
            },
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            return data.get("messages", [{}])[0].get("id", "")