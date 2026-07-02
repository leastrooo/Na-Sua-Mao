import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.models import Usuario, LogAuditoria

SECRET_KEY = os.getenv("SECRET_KEY", "na-sua-mao-secret-key-dev-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8


def hash_senha(senha: str) -> str:
    pwd_bytes = senha.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verificar_senha(senha: str, hash_str: str) -> bool:
    return bcrypt.checkpw(senha.encode('utf-8'), hash_str.encode('utf-8'))


def criar_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decodificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def get_usuario_atual(request: Request, db: Session = Depends(get_db)) -> Optional[Usuario]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decodificar_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return db.query(Usuario).filter(Usuario.id_usuario == int(user_id)).first()

def require_login(request: Request, db: Session = Depends(get_db)) -> Usuario:
    usuario = get_usuario_atual(request, db)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    if usuario.status_conta != "ativo":
        raise HTTPException(status_code=403, detail="Conta suspensa ou inativa.")
    return usuario

def require_admin(request: Request, db: Session = Depends(get_db)) -> Usuario:
    usuario = require_login(request, db)
    if not usuario.is_admin:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    return usuario

def registrar_log(db: Session, usuario_id: Optional[int], acao: str, detalhe: str = None, ip: str = None):
    log = LogAuditoria(usuario_id=usuario_id, acao=acao, detalhe=detalhe, ip=ip)
    db.add(log)
    db.commit()