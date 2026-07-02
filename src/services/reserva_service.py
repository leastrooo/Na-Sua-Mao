from datetime import datetime, date
import hashlib
from sqlalchemy.orm import Session
from models.models import Reserva, Ferramenta, Retirada, Devolucao, Contrato, StatusReserva, StatusFerramenta

def calcular_dias(data_inicio: date, data_fim: date) -> int:
    return max((data_fim - data_inicio).days, 1)

def solicitar_aluguel(db: Session, ferramenta_id: int, locatario_id: int, data_inicio_str: str, data_fim_str: str) -> dict:
    ferramenta = db.query(Ferramenta).filter(Ferramenta.id_ferramenta == ferramenta_id).first()
    if not ferramenta:
        return {"erro": "Ferramenta não encontrada."}

    if ferramenta.id_locador == locatario_id:
        return {"erro": "Você não pode alugar sua própria ferramenta."}

    try:
        d_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
        d_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
    except ValueError:
        return {"erro": "Formato de data inválido."}

    if d_inicio < date.today():
        return {"erro": "A data de início não pode ser no passado."}
    if d_fim < d_inicio:
        return {"erro": "A data de devolução não pode ser anterior à data de início."}

    
    conflito = db.query(Reserva).filter(
        Reserva.id_ferramenta == ferramenta_id,
        Reserva.status_reserva.in_([StatusReserva.CONFIRMADO, StatusReserva.EM_USO]),
        Reserva.data_prevista_inicio <= d_fim,
        Reserva.data_prevista_fim >= d_inicio
    ).first()

    if conflito:
        return {"erro": "Esta ferramenta já está reservada para o período selecionado."}

    dias = calcular_dias(d_inicio, d_fim)
    total = dias * float(ferramenta.preco_diaria)

    reserva = Reserva(
        id_locatario=locatario_id,
        id_ferramenta=ferramenta_id,
        data_prevista_inicio=d_inicio,
        data_prevista_fim=d_fim,
        valor_total_calculado=total,
        status_reserva=StatusReserva.AGUARDANDO
    )
    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    return {"reserva": reserva}

def confirmar_aluguel(db: Session, reserva_id: int, locador_id: int) -> dict:
    reserva = db.query(Reserva).filter(Reserva.id_reserva == reserva_id).first()
    if not reserva or reserva.ferramenta.id_locador != locador_id:
        return {"erro": "Reserva não encontrada ou sem permissão."}

    reserva.status_reserva = StatusReserva.CONFIRMADO
    
    
    hash_base = f"RESERVA_{reserva.id_reserva}_{reserva.id_locatario}_{datetime.utcnow().timestamp()}"
    hash_seg = hashlib.sha256(hash_base.encode()).hexdigest()
    
    contrato = Contrato(
        id_reserva=reserva.id_reserva,
        aceite_digital=True,
        hash_seguranca=hash_seg
    )
    db.add(contrato)
    db.commit()
    return {"reserva": reserva}

def registrar_entrega(db: Session, reserva_id: int, locador_id: int) -> dict:
    reserva = db.query(Reserva).filter(Reserva.id_reserva == reserva_id).first()
    if not reserva or reserva.ferramenta.id_locador != locador_id:
        return {"erro": "Sem permissão ou reserva inválida."}

    reserva.status_reserva = StatusReserva.EM_USO
    reserva.ferramenta.status_ferramenta = StatusFerramenta.ALUGADA
    
    retirada = Retirada(id_reserva=reserva_id, obs_estado_entrega="Entregue em perfeito estado de funcionamento.")
    db.add(retirada)
    db.commit()
    return {"reserva": reserva}

def registrar_devolucao(db: Session, reserva_id: int, locador_id: int, condicao: str) -> dict:
    reserva = db.query(Reserva).filter(Reserva.id_reserva == reserva_id).first()
    if not reserva or reserva.ferramenta.id_locador != locador_id:
        return {"erro": "Sem permissão ou reserva inválida."}

    reserva.status_reserva = StatusReserva.FINALIZADO
    reserva.ferramenta.status_ferramenta = StatusFerramenta.DISPONIVEL
    
    devolucao = Devolucao(id_reserva=reserva_id, obs_estado_retorno=condicao)
    db.add(devolucao)
    db.commit()
    return {"reserva": reserva}

def cancelar_reserva(db: Session, reserva_id: int, usuario_id: int, motivo: str) -> dict:
    reserva = db.query(Reserva).filter(Reserva.id_reserva == reserva_id).first()
    if not reserva:
        return {"erro": "Reserva não encontrada."}

    if reserva.ferramenta.id_locador != usuario_id and reserva.id_locatario != usuario_id:
        return {"erro": "Sem permissão."}

    if reserva.status_reserva not in [StatusReserva.AGUARDANDO, StatusReserva.CONFIRMADO]:
        return {"erro": "Não é possível cancelar nesta fase."}

    reserva.status_reserva = StatusReserva.CANCELADO
    reserva.motivo_cancelamento = motivo
    db.commit()
    return {"reserva": reserva}