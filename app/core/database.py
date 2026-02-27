from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    # Importa todos os models para registrar as tabelas no Base
    from app.models import Tenant, Patient, MessageLog
    Base.metadata.create_all(bind=engine)
    print("✅ Todas as tabelas criadas/verficadas com sucesso!")