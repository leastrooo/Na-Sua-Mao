from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from src.middlewares.auth import criar_token, get_usuario_atual, require_login, registrar_log
from src.services.usuario_service import cadastrar_usuario, autenticar_usuario, pode_excluir_conta
from src.integrations.storage_service import salvar_imagem
from models.models import Usuario

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    usuario = get_usuario_atual(request, db)
    if usuario:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "erro": None})

@router.post("/login")
async def login(request: Request, email: str = Form(...), senha: str = Form(...), db: Session = Depends(get_db)):
    resultado = autenticar_usuario(db, email, senha)
    if "erro" in resultado:
        return templates.TemplateResponse("login.html", {"request": request, "erro": resultado["erro"]})

    usuario = resultado["usuario"]
    token = criar_token({"sub": str(usuario.id_usuario)})
    registrar_log(db, usuario.id_usuario, "LOGIN", "Login realizado", request.client.host if request.client else "N/A")

    response = RedirectResponse("/", status_code=302)
    response.set_cookie("access_token", token, httponly=True, max_age=28800)
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response

@router.get("/cadastro", response_class=HTMLResponse)
async def cadastro_page(request: Request, db: Session = Depends(get_db)):
    usuario = get_usuario_atual(request, db)
    if usuario:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("cadastro.html", {"request": request, "erro": None})

@router.post("/cadastro")
async def cadastro(
    request: Request, nome: str = Form(...), email: str = Form(...), senha: str = Form(...),
    cpf: str = Form(...), telefone: str = Form(""), endereco: str = Form(""),
    bairro: str = Form(""), data_nascimento: str = Form(...), db: Session = Depends(get_db)
):
    dados = {
        "nome": nome, "email": email, "senha": senha, "cpf": cpf,
        "telefone": telefone, "endereco": endereco, "bairro": bairro,
        "data_nascimento": data_nascimento
    }
    resultado = cadastrar_usuario(db, dados)
    if "erro" in resultado:
        return templates.TemplateResponse("cadastro.html", {"request": request, "erro": resultado["erro"]})

    usuario = resultado["usuario"]
    token = criar_token({"sub": str(usuario.id_usuario)})
    response = RedirectResponse("/", status_code=302)
    response.set_cookie("access_token", token, httponly=True, max_age=28800)
    return response


@router.get("/perfil", response_class=HTMLResponse)
async def perfil(request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    from models.models import Avaliacao
    avaliacoes = db.query(Avaliacao).filter(Avaliacao.id_avaliado == usuario.id_usuario).order_by(Avaliacao.id_avaliacao.desc()).limit(5).all()
    return templates.TemplateResponse("perfil.html", {
        "request": request, "usuario": usuario, "avaliacoes": avaliacoes, "erro": None, "sucesso": None
    })

@router.post("/perfil")
async def perfil_update(
    request: Request, telefone: str = Form(""), endereco: str = Form(""), bairro: str = Form(""),
    foto: UploadFile = File(None), db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)
):
    usuario.telefone = telefone
    usuario.endereco = endereco
    usuario.bairro = bairro

    if foto and foto.filename:
        conteudo = await foto.read()
        if conteudo:
            caminho = salvar_imagem(conteudo, foto.filename)
            usuario.foto = caminho

    db.commit()
    from models.models import Avaliacao
    avaliacoes = db.query(Avaliacao).filter(Avaliacao.id_avaliado == usuario.id_usuario).order_by(Avaliacao.id_avaliacao.desc()).limit(5).all()
    return templates.TemplateResponse("perfil.html", {
        "request": request, "usuario": usuario, "avaliacoes": avaliacoes, "erro": None, "sucesso": "Perfil atualizado com sucesso!"
    })

@router.get("/perfil/excluir")
async def excluir_conta(request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    resultado = pode_excluir_conta(db, usuario.id_usuario)
    if not resultado["pode"]:
        from models.models import Avaliacao
        avaliacoes = db.query(Avaliacao).filter(Avaliacao.id_avaliado == usuario.id_usuario).all()
        return templates.TemplateResponse("perfil.html", {
            "request": request, "usuario": usuario, "avaliacoes": avaliacoes, "erro": resultado["motivo"], "sucesso": None
        })

    
    usuario.nome = f"Usuário {usuario.id_usuario} (excluído)"
    usuario.email = f"excluido_{usuario.id_usuario}@anonimo.com"
    usuario.telefone = None
    usuario.endereco = None
    usuario.cpf = f"000.000.000-{usuario.id_usuario:02d}"
    usuario.status_conta = "inativo"
    db.commit()

    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response