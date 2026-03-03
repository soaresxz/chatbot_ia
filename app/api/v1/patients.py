"""
Paths gerados (sem prefixo adicional no include_router):
  GET  /clinica/{tenant_id}/pacientes
  POST /clinica/{tenant_id}/pacientes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db

router = APIRouter(prefix="/clinica", tags=["pacientes"])


class CreatePatient(BaseModel):
    nome: str
    telefone: str


@router.get("/{tenant_id}/pacientes")
def list_patients(tenant_id: str, db: Session = Depends(get_db)):
    from app.models.patient import Patient

    patients = db.query(Patient).filter(Patient.tenant_id == tenant_id).all()
    return {
        "total": len(patients),
        "pacientes": [
            {
                "id": p.id,
                "nome": p.name,
                "telefone": p.phone,
                "criado_em": p.created_at.strftime("%d/%m/%Y %H:%M"),
            }
            for p in patients
        ],
    }


@router.post("/{tenant_id}/pacientes")
def create_patient(tenant_id: str, data: CreatePatient, db: Session = Depends(get_db)):
    from app.models.patient import Patient

    new_patient = Patient(
        tenant_id=tenant_id,
        name=data.nome,
        phone=data.telefone,
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return {
        "status": "success",
        "paciente_id": new_patient.id,
        "nome": new_patient.name,
        "telefone": new_patient.phone,
    }