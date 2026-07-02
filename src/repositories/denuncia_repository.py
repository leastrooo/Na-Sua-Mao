from sqlalchemy.orm import Session
from models.models import Denuncia, Reserva, StatusDenuncia, StatusReserva


def buscar_por_id(db: Session, denuncia_id: int) -> Denuncia | None:
    return db.query(Denuncia).filter(Denuncia.id_denuncia == denuncia_id).first()


def buscar_por_reserva(db: Session, reserva_id: int) -> Denuncia | None:
    return db.query(Denuncia).filter(Denuncia.id_reserva == reserva_id).first()


def listar_pendentes(db: Session) -> list[Denuncia]:
    return (
        db.query(Denuncia)
        .filter(Denuncia.status_denuncia.in_([StatusDenuncia.PENDENTE, StatusDenuncia.EM_ANALISE]))
        .order_by(Denuncia.id_denuncia.desc())
        .all()
    )


def criar(
    db: Session,
    reserva_id: int,
    denunciante_id: int,
    motivo: str,
    descricao: str,
    foto_evidencia: str | None = None,
) -> Denuncia:
    nova_denuncia = Denuncia(
        id_reserva=reserva_id,
        id_denunciante=denunciante_id,
        motivo=motivo,
        descricao=descricao,
        foto_evidencia=foto_evidencia,
        status_denuncia=StatusDenuncia.PENDENTE,
    )
    db.add(nova_denuncia)

    reserva = db.query(Reserva).filter(Reserva.id_reserva == reserva_id).first()
    if reserva:
        reserva.status_reserva = StatusReserva.EM_DISPUTA

    db.commit()
    db.refresh(nova_denuncia)
    return nova_denuncia


def resolver(db: Session, denuncia_id: int, resolucao: str) -> Denuncia | None:
    denuncia = buscar_por_id(db, denuncia_id)
    if not denuncia:
        return None

    denuncia.status_denuncia = StatusDenuncia.RESOLVIDA
    denuncia.resolucao = resolucao

    reserva = db.query(Reserva).filter(Reserva.id_reserva == denuncia.id_reserva).first()
    if reserva:
        reserva.status_reserva = StatusReserva.FINALIZADO

    db.commit()
    db.refresh(denuncia)
    return denuncia