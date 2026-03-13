import os
from sqlalchemy import text, inspect
from app.core.database import engine, Base

# Importa todos os modulos para registrar no Base.metadata
from app.models.tenant import Tenant
from app.models.patient import Patient
from app.models.user import User
from app.models.appointment import Appointment
from app.models.clinic_hours import ClinicHours
from app.models.conversation_status import ConversationStatus
from app.models.message_log import MessageLog
from app.models.service import Service

print("🔄 Aplicando migrações pendentes no banco de dados...")

# 1. Cria as tabelas que ainda não existem (ex: clinic_hours)
print("1️⃣ Criando tabelas ausentes (como clinic_hours)...")
Base.metadata.create_all(bind=engine)
print("✅ Tabelas verificadas/criadas.")

# 2. Adiciona colunas ausentes em tabelas existentes
with engine.begin() as conn:
    inspector = inspect(engine)
    
    # Atualiza conversation_status
    conv_columns = [col['name'] for col in inspector.get_columns('conversation_status')]
    if 'pending_confirmation' not in conv_columns:
        print("2️⃣ Adicionando coluna 'pending_confirmation' (JSONB) em conversation_status...")
        conn.execute(text("ALTER TABLE conversation_status ADD COLUMN pending_confirmation JSONB;"))
        print("✅ Coluna pending_confirmation adicionada com sucesso.")
    else:
        print("✅ Coluna pending_confirmation já existe.")

    if 'message_log' not in conv_columns:
        print("2.5️⃣ Adicionando coluna 'message_log' (JSONB) em conversation_status...")
        conn.execute(text("ALTER TABLE conversation_status ADD COLUMN message_log JSONB DEFAULT '[]'::jsonb;"))
        print("✅ Coluna message_log adicionada com sucesso.")
    else:
        print("✅ Coluna message_log já existe.")

    # Atualiza appointments
    appt_columns = [col['name'] for col in inspector.get_columns('appointments')]
    
    if 'value' not in appt_columns:
        print("3️⃣ Adicionando coluna 'value' (FLOAT) em appointments...")
        conn.execute(text("ALTER TABLE appointments ADD COLUMN value FLOAT DEFAULT 0.0;"))
        print("✅ Coluna value adicionada com sucesso.")
    else:
        print("✅ Coluna value já existe.")
        
    if 'confirmed_at' not in appt_columns:
        print("4️⃣ Adicionando coluna 'confirmed_at' (TIMESTAMP) em appointments...")
        conn.execute(text("ALTER TABLE appointments ADD COLUMN confirmed_at TIMESTAMP;"))
        print("✅ Coluna confirmed_at adicionada com sucesso.")
    else:
        print("✅ Coluna confirmed_at já existe.")

print("\n🎉 Migração agendamento/status concluída! Pode iniciar o servidor.")
