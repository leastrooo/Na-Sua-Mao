from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from src.middlewares.auth import require_login, registrar_log, get_usuario_atual
from src.services.reserva_service import (
    solicitar_aluguel, confirmar_aluguel, registrar_entrega,
    registrar_devolucao, cancelar_reserva
)
from src.services.avaliacao_service import avaliar_experiencia
from src.repositories import denuncia_repository
from models.models import Reserva, StatusReserva, Mensagem, Avaliacao, Ferramenta, Denuncia, Usuario

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/reservas/solicitar")
async def solicitar(
    request: Request,
    ferramenta_id: int = Form(...),
    data_inicio: str = Form(...),
    data_fim: str = Form(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_login)
):
    resultado = solicitar_aluguel(db, ferramenta_id, usuario.id_usuario, data_inicio, data_fim)
    if "erro" in resultado:
        ferramenta = db.query(Ferramenta).filter(Ferramenta.id_ferramenta == ferramenta_id).first()
        avaliacoes_locador = db.query(Avaliacao).filter(Avaliacao.id_avaliado == ferramenta.id_locador).limit(5).all()
        return templates.TemplateResponse("ferramenta_detalhe.html", {
            "request": request, "usuario": usuario,
            "ferramenta": ferramenta, "avaliacoes_locador": avaliacoes_locador,
            "erro": resultado["erro"]
        })

    registrar_log(db, usuario.id_usuario, "SOLICITAR_ALUGUEL",
                  f"Reserva #{resultado['reserva'].id_reserva}", request.client.host if request.client else "N/A")
    return RedirectResponse("/meus-alugueis", status_code=302)

@router.get("/meus-alugueis", response_class=HTMLResponse)
async def meus_alugueis(request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    como_locatario = db.query(Reserva).filter(
        Reserva.id_locatario == usuario.id_usuario
    ).order_by(Reserva.id_reserva.desc()).all()

    ferramentas_ids = [f.id_ferramenta for f in db.query(Ferramenta).filter(Ferramenta.id_locador == usuario.id_usuario).all()]
    como_locador = db.query(Reserva).filter(
        Reserva.id_ferramenta.in_(ferramentas_ids)
    ).order_by(Reserva.id_reserva.desc()).all() if ferramentas_ids else []

    return templates.TemplateResponse("meus_alugueis.html", {
        "request": request, "usuario": usuario,
        "como_locatario": como_locatario, "como_locador": como_locador,
        "StatusReserva": StatusReserva
    })

@router.get("/reservas/{reserva_id}", response_class=HTMLResponse)
async def detalhe_reserva(request: Request, reserva_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    reserva = db.query(Reserva).filter(Reserva.id_reserva == reserva_id).first()
    if not reserva:
        return RedirectResponse("/meus-alugueis", status_code=302)

    eh_locador = reserva.ferramenta.id_locador == usuario.id_usuario
    eh_locatario = reserva.id_locatario == usuario.id_usuario
    if not eh_locador and not eh_locatario:
        return RedirectResponse("/meus-alugueis", status_code=302)

    mensagens = db.query(Mensagem).filter(Mensagem.id_reserva == reserva_id).order_by(Mensagem.id_mensagem.asc()).all()
    avaliacao_usuario = db.query(Avaliacao).filter(
        Avaliacao.id_reserva == reserva_id, Avaliacao.id_avaliador == usuario.id_usuario
    ).first()
    denuncia = denuncia_repository.buscar_por_reserva(db, reserva_id)

    return templates.TemplateResponse("reserva_detalhe.html", {
        "request": request, "usuario": usuario, "reserva": reserva,
        "eh_locador": eh_locador, "eh_locatario": eh_locatario,
        "mensagens": mensagens, "avaliacao_usuario": avaliacao_usuario,
        "denuncia": denuncia, "StatusReserva": StatusReserva,
        "erro": None, "sucesso": None
    })

@router.post("/reservas/{reserva_id}/confirmar")
async def confirmar(request: Request, reserva_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    confirmar_aluguel(db, reserva_id, usuario.id_usuario)
    registrar_log(db, usuario.id_usuario, "CONFIRMAR_RESERVA", f"Reserva #{reserva_id}", request.client.host if request.client else "N/A")
    return RedirectResponse(f"/reservas/{reserva_id}", status_code=302)

@router.post("/reservas/{reserva_id}/entregar")
async def entregar(request: Request, reserva_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    registrar_entrega(db, reserva_id, usuario.id_usuario)
    registrar_log(db, usuario.id_usuario, "REGISTRAR_ENTREGA", f"Reserva #{reserva_id}", request.client.host if request.client else "N/A")
    return RedirectResponse(f"/reservas/{reserva_id}", status_code=302)

@router.post("/reservas/{reserva_id}/devolver")
async def devolver(request: Request, reserva_id: int, condicao: str = Form("Bom estado"), db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    registrar_devolucao(db, reserva_id, usuario.id_usuario, condicao)
    registrar_log(db, usuario.id_usuario, "REGISTRAR_DEVOLUCAO", f"Reserva #{reserva_id}", request.client.host if request.client else "N/A")
    return RedirectResponse(f"/reservas/{reserva_id}", status_code=302)

@router.post("/reservas/{reserva_id}/cancelar")
async def cancelar(request: Request, reserva_id: int, motivo: str = Form(...), db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    cancelar_reserva(db, reserva_id, usuario.id_usuario, motivo)
    registrar_log(db, usuario.id_usuario, "CANCELAR_RESERVA", f"Reserva #{reserva_id} - {motivo}", request.client.host if request.client else "N/A")
    return RedirectResponse(f"/reservas/{reserva_id}", status_code=302)

@router.post("/reservas/{reserva_id}/mensagem")
async def enviar_mensagem(request: Request, reserva_id: int, conteudo: str = Form(...), db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    reserva = db.query(Reserva).filter(Reserva.id_reserva == reserva_id).first()
    if not reserva:
        return RedirectResponse("/meus-alugueis", status_code=302)

    destinatario_id = reserva.ferramenta.id_locador if reserva.id_locatario == usuario.id_usuario else reserva.id_locatario
    msg = Mensagem(
        id_reserva=reserva_id,
        id_remetente=usuario.id_usuario,
        conteudo=conteudo
    )
    db.add(msg)
    db.commit()
    return RedirectResponse(f"/reservas/{reserva_id}", status_code=302)

@router.post("/reservas/{reserva_id}/avaliar")
async def avaliar(request: Request, reserva_id: int, nota: int = Form(...), comentario: str = Form(...), db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    resultado = avaliar_experiencia(db, reserva_id, usuario.id_usuario, nota, comentario)
    reserva = db.query(Reserva).filter(Reserva.id_reserva == reserva_id).first()
    mensagens = db.query(Mensagem).filter(Mensagem.id_reserva == reserva_id).all()
    avaliacao_usuario = db.query(Avaliacao).filter(Avaliacao.id_reserva == reserva_id, Avaliacao.id_avaliador == usuario.id_usuario).first()
    denuncia = denuncia_repository.buscar_por_reserva(db, reserva_id)
    eh_locador = reserva.ferramenta.id_locador == usuario.id_usuario

    if "erro" in resultado:
        return templates.TemplateResponse("reserva_detalhe.html", {
            "request": request, "usuario": usuario, "reserva": reserva,
            "eh_locador": eh_locador, "eh_locatario": not eh_locador,
            "mensagens": mensagens, "avaliacao_usuario": avaliacao_usuario,
            "denuncia": denuncia, "StatusReserva": StatusReserva,
            "erro": resultado["erro"], "sucesso": None
        })

    return RedirectResponse(f"/reservas/{reserva_id}", status_code=302)

@router.post("/reservas/{reserva_id}/denuncia")
async def abrir_denuncia_route(request: Request, reserva_id: int, motivo: str = Form(...), descricao: str = Form(...), db: Session = Depends(get_db), usuario: Usuario = Depends(require_login)):
    denuncia_repository.criar(db, reserva_id, usuario.id_usuario, motivo, descricao)
    registrar_log(db, usuario.id_usuario, "ABRIR_DENUNCIA", f"Reserva #{reserva_id} - {motivo}", request.client.host if request.client else "N/A")
    return RedirectResponse(f"/reservas/{reserva_id}", status_code=302)