from __future__ import annotations  # ← ESSA LINHA RESOLVE 90% dos erros de IDE

import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import update
from app.core.config import settings

# Prioridade: Railway > settings
DATABASE_URL = os.getenv("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL não encontrada! Verifique no Railway.")

# Converte para asyncpg (obrigatório no Railway)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()

# Dependency para FastAPI
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Reset automático do modo humano (corrigido)
async def reset_human_modes():
    from app.models.tenant import Tenant   # ← ajuste se o caminho do seu Tenant for diferente

    async with AsyncSessionLocal() as session:
        stmt = update(Tenant).values(
            human_mode_active=False,
            human_mode_until=None
        )
        await session.execute(stmt)
        await session.commit()
    print("✅ Modo humano resetado para todos os tenants!")

# Criar tabelas + reset
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Todas as tabelas criadas/verficadas com sucesso!")

    await reset_human_modes()   # reset automático no startup