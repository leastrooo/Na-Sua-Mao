import os
import sys
from datetime import datetime, date 


sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import engine, Base



import models.models  


from src.controllers.auth_controller import router as auth_router
from src.controllers.ferramenta_controller import router as ferramenta_router
from src.controllers.reserva_controller import router as reserva_router
from src.controllers.admin_controller import router as admin_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Na Sua Mão",
    description="Plataforma de aluguel de ferramentas entre vizinhos — UCB 2026",
    version="2.0.0"
)


os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(auth_router)
app.include_router(ferramenta_router)
app.include_router(reserva_router)
app.include_router(admin_router)



@app.on_event("startup")
def criar_dados_iniciais():
    """Cria categorias base e usuários demo apenas se o banco estiver vazio"""
    from database import SessionLocal
    from models.models import Usuario, Categoria
    
    db = SessionLocal()
    
    
    cat_nomes = ["Jardinagem", "Construção", "Limpeza", "Elétrica", "Automotiva", "Outros"]
    for nome in cat_nomes:
        if not db.query(Categoria).filter(Categoria.nome_categoria == nome).first():
            db.add(Categoria(nome_categoria=nome))
    
    
    admin = db.query(Usuario).filter(Usuario.email == "admin@nasua.mao").first()
    if not admin:
        from src.middlewares.auth import hash_senha
        admin = Usuario(
            nome="Administrador",
            email="admin@nasua.mao",
            senha=hash_senha("admin123"),
            cpf="000.000.000-00",
            data_nascimento=date(1990, 1, 1), 
            is_admin=True,
            status_conta="ativo"
        )
        db.add(admin)
    
    db.commit()
    db.close()
##from src.controllers import avaliacao_controller
##app.include_router(avaliacao_controller.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
