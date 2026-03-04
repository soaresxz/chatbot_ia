from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.auth import hash_password, verify_password, create_access_token, get_current_user, require_admin
from app.models.user import User
from app.models.tenant import Tenant

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    role: str = "clinic_user"
    tenant_id: str | None = None


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email, User.is_active == True).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    # ✅ Busca o plano do tenant para incluir no token
    plan = "basic"
    if user.tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        if tenant:
            plan = tenant.plan or "basic"

    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "plan": plan,  # ✅ incluído no JWT
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "plan": plan,  # ✅ incluído na resposta
        }
    }


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email já cadastrado")
    new_user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        role=data.role,
        tenant_id=data.tenant_id if data.role == "clinic_user" else None,
    )
    db.add(new_user)
    db.commit()
    return {"status": "success", "user_id": new_user.id}


@router.get("/me")
def me(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    plan = "basic"
    if current_user.tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if tenant:
            plan = tenant.plan or "basic"
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "plan": plan,
    }


@router.post("/create-first-admin")
def create_first_admin(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.role == "super_admin").first():
        raise HTTPException(403, "Já existe um admin. Use /auth/register.")
    new_admin = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        role="super_admin",
    )
    db.add(new_admin)
    db.commit()
    return {"status": "success", "message": "Admin criado. Endpoint desativado."}