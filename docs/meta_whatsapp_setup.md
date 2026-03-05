# Como conectar um número oficial WhatsApp (Meta Cloud API)

## Pré-requisitos
- Conta no [Meta Business Suite](https://business.facebook.com)
- Número de telefone dedicado (não pode estar associado a outro WhatsApp)
- App criado no [Meta Developers](https://developers.facebook.com)

---

## 1. Criar o App no Meta Developers

1. Acesse [developers.facebook.com](https://developers.facebook.com)
2. Clique em **Meus Apps → Criar App**
3. Selecione **Business** como tipo
4. Adicione o produto **WhatsApp** ao app

---

## 2. Adicionar o número de telefone

1. No painel do app → **WhatsApp → Getting Started**
2. Clique em **Adicionar número de telefone**
3. Siga o processo de verificação via SMS ou ligação
4. Anote o **Phone Number ID** (você vai precisar)

---

## 3. Gerar o Access Token permanente

1. No painel → **WhatsApp → Configuração**
2. Clique em **Gerar token de acesso permanente**
3. Salve o token — ele não será exibido novamente

---

## 4. Configurar o Webhook

1. No painel → **WhatsApp → Configuração → Webhook**
2. Clique em **Editar**
3. Preencha:
   - **URL do Callback:** `https://chatbotia-production.up.railway.app/api/v1/meta/webhook`
   - **Token de verificação:** o valor definido em `META_VERIFY_TOKEN` no Railway
4. Clique em **Verificar e Salvar**
5. Assine os campos: `messages`

---

## 5. Configurar variáveis no Railway

No serviço do backend, adicione as variáveis:

```
META_VERIFY_TOKEN=seu_token_de_verificacao_aqui
META_APP_SECRET=seu_app_secret_aqui
```

---

## 6. Configurar o tenant para usar Meta

No banco, atualize o tenant do cliente:

```sql
UPDATE tenants SET
  whatsapp_provider = 'meta',
  meta_phone_number_id = 'SEU_PHONE_NUMBER_ID',
  meta_access_token = 'SEU_ACCESS_TOKEN'
WHERE id = 'id_do_tenant';
```

Ou via endpoint (quando implementado no admin):
```json
PATCH /admin/tenants/{id}/provider
{
  "provider": "meta",
  "meta_phone_number_id": "...",
  "meta_access_token": "..."
}
```

---

## 7. Templates de mensagem (obrigatório para mensagens proativas)

Para enviar mensagens **fora da janela de 24h** (ex: confirmação de agendamento), é necessário usar templates aprovados pela Meta.

### Criar um template

1. No painel → **WhatsApp → Modelos de mensagem → Criar modelo**
2. Preencha:
   - **Nome:** `confirmacao_agendamento`
   - **Categoria:** Utilitário
   - **Idioma:** Português (BR)
   - **Corpo:** `Olá! Seu agendamento com {{1}} está confirmado para {{2}}. Até lá! 😊`
3. Envie para aprovação (geralmente 24-48h)

### Usar o template no código

```python
from app.services.whatsapp.meta_provider import MetaProvider

provider = MetaProvider(phone_number_id="...", access_token="...")
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
```

---

## 8. Botões interativos

Para confirmação de agendamento com botões:

```python
await provider.send_interactive_buttons(
    to="+5511999999999",
    body_text="Confirmar agendamento para 15/03 às 10h?",
    buttons=[
        {"id": "confirm", "title": "✅ Confirmar"},
        {"id": "cancel",  "title": "❌ Cancelar"},
    ]
)
```

> ⚠️ Botões interativos só funcionam dentro da janela de 24h ou com templates aprovados.

---

## Estrutura de provedores

```
app/services/whatsapp/
├── provider.py          # Interface base (ABC)
├── twilio_provider.py   # Twilio Sandbox (desenvolvimento)
├── meta_provider.py     # Meta Cloud API (produção)
└── provider_factory.py  # Seleciona provedor por tenant
```

Cada tenant pode usar um provedor diferente — basta configurar `whatsapp_provider` no banco.