"""
Migração: adiciona coluna api_key na tabela tenants
e gera chaves para todos os tenants existentes.

Rodar UMA VEZ, antes ou depois do deploy:
    python migrate_add_api_key.py
"""
import os
import secrets
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL não encontrada")

# Corrige caracteres especiais na senha da URL
from urllib.parse import urlparse, quote, urlunparse
parsed = urlparse(DATABASE_URL)
if parsed.password:
    safe_password = quote(parsed.password, safe="")
    netloc = f"{parsed.username}:{safe_password}@{parsed.hostname}"
    if parsed.port:
        netloc += f":{parsed.port}"
    DATABASE_URL = urlunparse(parsed._replace(netloc=netloc))

engine = create_engine(DATABASE_URL)

def generate_api_key() -> str:
    return f"sk_{secrets.token_urlsafe(36)}"

with engine.begin() as conn:
    # 1. Adiciona a coluna (ignora erro se já existir)
    try:
        conn.execute(text("ALTER TABLE tenants ADD COLUMN api_key VARCHAR UNIQUE"))
        print("✅ Coluna api_key adicionada")
    except Exception as e:
        print(f"⚠️  Coluna já existe ou erro: {e}")

    # 2. Gera api_key para todos os tenants que ainda não têm
    rows = conn.execute(text("SELECT id FROM tenants WHERE api_key IS NULL")).fetchall()
    for row in rows:
        key = generate_api_key()
        conn.execute(
            text("UPDATE tenants SET api_key = :key WHERE id = :id"),
            {"key": key, "id": row[0]}
        )
        print(f"🔑 {row[0]} → {key}")

    print(f"\n✅ Migração concluída. {len(rows)} tenant(s) atualizados.")
    print("⚠️  Salve as chaves acima — elas não serão exibidas novamente!")