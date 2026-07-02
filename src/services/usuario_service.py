from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from models.models import Usuario, Reserva, StatusReserva, Denuncia, StatusDenuncia
from src.middlewares.auth import hash_senha, verificar_senha
from src.integrations.cpf_service import validar_cpf_externo

def calcular_idade(data_nasc_obj: date) -> int:
    
    hoje = date.today()
    return hoje.year - data_nasc_obj.year - ((hoje.month, hoje.day) < (data_nasc_obj.month, data_nasc_obj.day))

def cadastrar_usuario(db: Session, dados: dict) -> dict:
    
    email_normalizado = dados["email"].lower().strip()
    
    if db.query(Usuario).filter(func.lower(Usuario.email) == email_normalizado).first():
        return {"erro": "E-mail já cadastrado."}

    if db.query(Usuario).filter(Usuario.cpf == dados["cpf"]).first():
        return {"erro": "CPF já cadastrado."}

    cpf_valido = validar_cpf_externo(dados["cpf"])
    if not cpf_valido:
        return {"erro": "CPF inválido ou não encontrado na Receita Federal."}

    
    try:
        data_nasc_obj = datetime.strptime(dados["data_nascimento"], "%Y-%m-%d").date()
    except ValueError:
        return {"erro": "Formato de data inválido."}

    if calcular_idade(data_nasc_obj) < 18:
        return {"erro": "É necessário ter pelo menos 18 anos para se cadastrar."}

    usuario = Usuario(
        nome=dados["nome"],
        email=email_normalizado,
        senha=hash_senha(dados["senha"]),
        cpf=dados["cpf"],
        telefone=dados.get("telefone"),
        endereco=dados.get("endereco"),
        bairro=dados.get("bairro"),
        data_nascimento=data_nasc_obj, 
        status_conta="ativo"
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"usuario": usuario}

def autenticar_usuario(db: Session, email: str, senha: str) -> dict:
    email_normalizado = email.lower().strip()
    usuario = db.query(Usuario).filter(func.lower(Usuario.email) == email_normalizado).first()
    
    if not usuario or not verificar_senha(senha, usuario.senha):
        return {"erro": "E-mail ou senha incorretos."}
    if usuario.status_conta == "suspenso":
        return {"erro": "Conta suspensa. Entre em contato com o suporte."}
    if usuario.status_conta == "inativo":
        return {"erro": "Conta inativa."}
    
    return {"usuario": usuario}

def pode_excluir_conta(db: Session, usuario_id: int) -> dict:
    
    status_bloqueantes = [StatusReserva.AGUARDANDO, StatusReserva.CONFIRMADO, StatusReserva.EM_USO]
    
    reservas_ativas = db.query(Reserva).filter(
        Reserva.id_locatario == usuario_id,
        Reserva.status_reserva.in_(status_bloqueantes)
    ).count()
    if reservas_ativas > 0:
        return {"pode": False, "motivo": "Você possui transações ativas em andamento."}

    denuncias = db.query(Denuncia).filter(
        Denuncia.id_denunciante == usuario_id,
        Denuncia.status_denuncia.in_([StatusDenuncia.PENDENTE, StatusDenuncia.EM_ANALISE])
    ).count()
    if denuncias > 0:
        return {"pode": False, "motivo": "Você possui denúncias em análise."}

    return {"pode": True}

def atualizar_reputacao(db: Session, usuario_id: int):
    
    from models.models import Avaliacao
    avaliacoes = db.query(Avaliacao).filter(Avaliacao.id_avaliado == usuario_id).all()
    if avaliacoes:
        media = sum(a.nota for a in avaliacoes) / len(avaliacoes)
        usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
        if usuario:
            usuario.reputacao_acumulada = round(media, 1)
            usuario.total_alugueis = len(avaliacoes)
            db.commit()