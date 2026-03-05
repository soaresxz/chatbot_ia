"""
Seleciona o provedor WhatsApp correto com base no tenant.

Cada tenant pode ter seu próprio provedor configurado:
  - "twilio" → Twilio Sandbox (padrão para desenvolvimento)
  - "meta"   → WhatsApp Business Cloud API (produção)
"""
from app.services.whatsapp.provider import WhatsAppProvider


def get_provider(tenant) -> WhatsAppProvider:
    """
    Retorna o provedor configurado para o tenant.
    Lê as credenciais dos campos do próprio tenant.
    """
    provider_name = getattr(tenant, "whatsapp_provider", None) or "twilio"

    if provider_name == "meta":
        from app.services.whatsapp.meta_provider import MetaProvider

        phone_number_id = getattr(tenant, "meta_phone_number_id", None)
        access_token = getattr(tenant, "meta_access_token", None)

        if not phone_number_id or not access_token:
            raise ValueError(
                f"Tenant '{tenant.id}' usa provider 'meta' mas não tem "
                "meta_phone_number_id ou meta_access_token configurados."
            )

        return MetaProvider(
            phone_number_id=phone_number_id,
            access_token=access_token,
        )

    # default: Twilio
    from app.services.whatsapp.twilio_provider import TwilioProvider
    return TwilioProvider()