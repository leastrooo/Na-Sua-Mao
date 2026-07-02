from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from src.middlewares.auth import require_login, get_usuario_atual, registrar_log
from src.services.ferramenta_service import cadastrar_ferramenta, buscar_ferramentas
from src.integrations.storage_service import salvar_imagem
from models.models import Ferramenta, StatusFerramenta, Usuario, Avaliacao, Categoria

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, busca: str = "", categoria: str = "", distancia: float = 5.0, db: Session = Depends(get_db)):
    usuario = get_usuario_atual(request, db)
    coord = (usuario.latitude, usuario.longitude) if (usuario and usuario.latitude) else None
    ferramentas = buscar_ferramentas(db, busca, categoria, distancia, coord)
    
    
    categorias_bd = db.query(Categoria).all()
    categorias_nomes = [c.nome_categoria for c in categorias_bd]

    return templates.TemplateResponse("index.html", {
        "request": request, "usuario": usuario, "ferramentas": ferramentas, 
        "categorias": categorias_nomes, "busca": busca, "categoria_sel": categoria
    })

@router.get("/ferramentas/nova", response_class=HTMLResponse)
async def nova_ferramenta_page(request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    categorias_bd = db.query(Categoria).all()
    categorias_nomes = [c.nome_categoria for c in categorias_bd]
    
    if not categorias_nomes:
        categorias_nomes = ["Jardinagem", "Construção", "Limpeza", "Elétrica", "Automotiva", "Outros"]

    return templates.TemplateResponse("nova_ferramenta.html", {
        "request": request, "usuario": usuario, "categorias": categorias_nomes, "erro": None
    })

@router.post("/ferramentas/nova")
async def nova_ferramenta(
    request: Request, nome: str = Form(...), descricao: str = Form(...),
    categoria: str = Form(...), valor_diaria: str = Form(...),
    foto1: UploadFile = File(None), foto2: UploadFile = File(None),
    foto3: UploadFile = File(None), foto4: UploadFile = File(None),
    foto5: UploadFile = File(None), db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_login)
):
    fotos = []
    for foto in [foto1, foto2, foto3, foto4, foto5]:
        if foto and foto.filename:
            conteudo = await foto.read()
            if conteudo:
                caminho = salvar_imagem(conteudo, foto.filename)
                fotos.append(caminho)
        else:
            fotos.append(None)

    dados = {
        "nome": nome, "descricao": descricao, "categoria": categoria, "valor_diaria": valor_diaria,
        "foto1": fotos[0], "foto2": fotos[1], "foto3": fotos[2], "foto4": fotos[3], "foto5": fotos[4]
    }

    resultado = cadastrar_ferramenta(db, dados, usuario.id_usuario)
    if "erro" in resultado:
        categorias_bd = db.query(Categoria).all()
        return templates.TemplateResponse("nova_ferramenta.html", {
            "request": request, "usuario": usuario,
            "categorias": [c.nome_categoria for c in categorias_bd], "erro": resultado["erro"]
        })

    registrar_log(db, usuario.id_usuario, "CADASTRAR_FERRAMENTA", f"Ferramenta: {nome}")
    return RedirectResponse("/minhas-ferramentas", status_code=302)

@router.get("/ferramentas/{ferramenta_id}", response_class=HTMLResponse)
async def detalhe_ferramenta(request: Request, ferramenta_id: int, db: Session = Depends(get_db)):
    usuario = get_usuario_atual(request, db)
    ferramenta = db.query(Ferramenta).filter(Ferramenta.id_ferramenta == ferramenta_id).first()
    
    if not ferramenta:
        return RedirectResponse("/", status_code=302)

    avaliacoes_locador = db.query(Avaliacao).filter(
        Avaliacao.id_avaliado == ferramenta.id_locador
    ).order_by(Avaliacao.id_avaliacao.desc()).limit(5).all()

    return templates.TemplateResponse("ferramenta_detalhe.html", {
        "request": request, "usuario": usuario,
        "ferramenta": ferramenta, "avaliacoes_locador": avaliacoes_locador
    })

@router.get("/minhas-ferramentas", response_class=HTMLResponse)
async def minhas_ferramentas(request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    ferramentas = db.query(Ferramenta).filter(Ferramenta.id_locador == usuario.id_usuario).all()
    return templates.TemplateResponse("minhas_ferramentas.html", {
        "request": request, "usuario": usuario, "ferramentas": ferramentas
    })

@router.post("/ferramentas/{ferramenta_id}/status")
async def alterar_status(
    request: Request, ferramenta_id: int, novo_status: str = Form(...), 
    db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)
):
    ferramenta = db.query(Ferramenta).filter(
        Ferramenta.id_ferramenta == ferramenta_id,
        Ferramenta.id_locador == usuario.id_usuario
    ).first()

    if ferramenta and novo_status in [s.value for s in StatusFerramenta]:
        ferramenta.status_ferramenta = novo_status
        db.commit()

    return RedirectResponse("/minhas-ferramentas", status_code=302)