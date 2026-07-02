from sqlalchemy.orm import Session
from models.models import Avaliacao, Reserva, StatusReserva, Denuncia, StatusDenuncia
from src.services.usuario_service import atualizar_reputacao

PALAVRAS_PROIBIDAS = ["idiota", "burro", "incompetente", "lixo", "merda", "porra", "desgraça"]

def validar_comentario(texto: str) -> bool:
    if not texto or len(texto.strip()) < 5:
        return False
    texto_lower = texto.lower()
    for palavra in PALAVRAS_PROIBIDAS:
        if palavra in texto_lower:
            return False
    return True

def avaliar_experiencia(db: Session, reserva_id: int, avaliador_id: int, nota: int, comentario: str) -> dict:
    reserva = db.query(Reserva).filter(Reserva.id_reserva == reserva_id).first()
    if not reserva:
        return {"erro": "Reserva não encontrada."}

    if reserva.status_reserva != StatusReserva.FINALIZADO:
        return {"erro": "Somente aluguéis finalizados podem ser avaliados."}

    if not validar_comentario(comentario):
        return {"erro": "O comentário contém palavras impróprias ou é curto demais."}

    avaliado_id = reserva.ferramenta.id_locador if reserva.id_locatario == avaliador_id else reserva.id_locatario

    avaliacao = Avaliacao(
        id_reserva=reserva_id,
        id_avaliador=avaliador_id,
        id_avaliado=avaliado_id,
        nota=nota,
        comentario=comentario
    )
    db.add(avaliacao)
    db.commit()

    atualizar_reputacao(db, avaliado_id)
    return {"avaliacao": avaliacao}

def abrir_denuncia(db: Session, reserva_id: int, denunciante_id: int, motivo: str, descricao: str) -> dict:
    reserva = db.query(Reserva).filter(Reserva.id_reserva == reserva_id).first()
    if not reserva:
        return {"erro": "Reserva não encontrada."}

    denuncia = Denuncia(
        id_reserva=reserva_id,
        id_denunciante=denunciante_id,
        motivo=motivo,
        descricao=descricao,
        status_denuncia=StatusDenuncia.PENDENTE
    )
    db.add(denuncia)
    reserva.status_reserva = StatusReserva.EM_DISPUTA
    db.commit()
    return {"denuncia": denuncia}

def resolver_denuncia(db: Session, denuncia_id: int, resolucao: str, admin_id: int) -> dict:
    denuncia = db.query(Denuncia).filter(Denuncia.id_denuncia == denuncia_id).first()
    if denuncia:
        denuncia.status_denuncia = StatusDenuncia.RESOLVIDA
        denuncia.resolucao = resolucao
        if denuncia.reserva:
            denuncia.reserva.status_reserva = StatusReserva.FINALIZADO
        db.commit()
        return {"denuncia": denuncia}
    return {"erro": "Denúncia não encontrada."}