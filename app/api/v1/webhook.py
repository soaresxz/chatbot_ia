from fastapi import APIRouter, Request, BackgroundTasks
from urllib.parse import parse_qs


from app.services.whatsapp.service import process_incoming_message

router = APIRouter(prefix="/twilio")


@router.post("/webhook")
async def twilio_webhook(request: Request, background_tasks: BackgroundTasks):
    # Lê o body raw para evitar perda
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    print(f"Raw body: {body_str}")  # Debug
    
    if not body_str:
        print("❌ Body vazio - problema de middleware ou ngrok")
        return "OK", 200
    
    data = parse_qs(body_str)
    from_number = data.get("From", [None])[0]
    body = data.get("Body", [None])[0]
    to_number = data.get("To", [None])[0]
    
    print(f"✅ From: {from_number}")
    print(f"✅ Body: {body}")
    print(f"✅ To:   {to_number}")

    if from_number and body:
        background_tasks.add_task(process_incoming_message, from_number, body, to_number)
    return "OK", 200



