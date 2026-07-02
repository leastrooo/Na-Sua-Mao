from sqlalchemy import Column, Integer, String, Float, Text, Date, DateTime, ForeignKey, Boolean, Enum as SAEnum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base

class TipoPerfil(str, enum.Enum):
    LOCADOR = "Locador"
    LOCATARIO = "Locatário"
    AMBOS = "Ambos"
    ADMIN = "Admin"

class Voltagem(str, enum.Enum):
    V110 = "110V"
    V220 = "220V"
    BIVOLT = "Bivolt"
    MANUAL = "Manual"

class EstadoConservacao(str, enum.Enum):
    NOVO = "Novo"
    BOM = "Bom estado"
    REGULAR = "Regular"
    RUIM = "Ruim"

class StatusFerramenta(str, enum.Enum):
    DISPONIVEL = "Disponível"
    ALUGADA = "Alugada"
    MANUTENCAO = "Em Manutenção"
    INATIVA = "Inativa"

class StatusReserva(str, enum.Enum):
    AGUARDANDO = "Aguardando aprovação"
    CONFIRMADO = "Confirmado"
    EM_USO = "Em Uso"
    FINALIZADO = "Finalizado"
    CANCELADO = "Cancelado"
    EM_DISPUTA = "Em Disputa"

class StatusDenuncia(str, enum.Enum):
    PENDENTE = "Pendente"
    EM_ANALISE = "Em Análise"
    RESOLVIDA = "Resolvida"
    ENCERRADA = "Encerrada"


class Categoria(Base):
    __tablename__ = "categorias"

    id_categoria = Column(Integer, primary_key=True, index=True)
    nome_categoria = Column(String(50), nullable=False)

    ferramentas = relationship("Ferramenta", back_populates="categoria")


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    senha = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False)
    cep = Column(String(9), nullable=True)
    telefone = Column(String(15), nullable=True)
    reputacao_acumulada = Column(Numeric(3, 1), default=0.0)
    tipo_perfil = Column(SAEnum(TipoPerfil), default=TipoPerfil.AMBOS)
    data_cadastro = Column(DateTime(timezone=True), server_default=func.now())
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    
    data_nascimento = Column(Date, nullable=False)  
    bairro = Column(String(100), nullable=True)
    endereco = Column(String(255), nullable=True)
    foto = Column(String(255), nullable=True)
    total_alugueis = Column(Integer, default=0)
    status_conta = Column(String(20), default="ativo")
    is_admin = Column(Boolean, default=False)

    ferramentas = relationship("Ferramenta", back_populates="locador")
    reservas_como_locatario = relationship("Reserva", back_populates="locatario", foreign_keys="Reserva.id_locatario")


class Ferramenta(Base):
    __tablename__ = "ferramentas"

    id_ferramenta = Column(Integer, primary_key=True, index=True)
    id_locador = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_categoria = Column(Integer, ForeignKey("categorias.id_categoria"), nullable=False)
    titulo = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=False)
    voltagem = Column(SAEnum(Voltagem), default=Voltagem.MANUAL)
    estado_conservacao = Column(SAEnum(EstadoConservacao), default=EstadoConservacao.BOM)
    preco_diaria = Column(Numeric(10, 2), nullable=False)
    status_ferramenta = Column(SAEnum(StatusFerramenta), default=StatusFerramenta.DISPONIVEL)

    
    foto1 = Column(String(255), nullable=True)
    foto2 = Column(String(255), nullable=True)
    foto3 = Column(String(255), nullable=True)
    foto4 = Column(String(255), nullable=True)
    foto5 = Column(String(255), nullable=True)

    locador = relationship("Usuario", back_populates="ferramentas")
    categoria = relationship("Categoria", back_populates="ferramentas")
    reservas = relationship("Reserva", back_populates="ferramenta")


class Reserva(Base):
    __tablename__ = "reservas"

    id_reserva = Column(Integer, primary_key=True, index=True)
    id_locatario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_ferramenta = Column(Integer, ForeignKey("ferramentas.id_ferramenta"), nullable=False)
    data_prevista_inicio = Column(Date, nullable=False)
    data_prevista_fim = Column(Date, nullable=False)
    valor_total_calculado = Column(Numeric(10, 2), nullable=False)
    status_reserva = Column(SAEnum(StatusReserva), default=StatusReserva.AGUARDANDO)
    data_solicitacao = Column(DateTime(timezone=True), server_default=func.now())
    motivo_cancelamento = Column(Text, nullable=True)

    locatario = relationship("Usuario", back_populates="reservas_como_locatario")
    ferramenta = relationship("Ferramenta", back_populates="reservas")
    
    
    contrato = relationship("Contrato", back_populates="reserva", uselist=False)
    retirada = relationship("Retirada", back_populates="reserva", uselist=False)
    devolucao = relationship("Devolucao", back_populates="reserva", uselist=False)


class Contrato(Base):
    __tablename__ = "contratos"

    id_contrato = Column(Integer, primary_key=True, index=True)
    id_reserva = Column(Integer, ForeignKey("reservas.id_reserva"), unique=True, nullable=False)
    aceite_digital = Column(Boolean, default=False)
    hash_seguranca = Column(String(255), nullable=False)
    data_geracao = Column(DateTime(timezone=True), server_default=func.now())

    reserva = relationship("Reserva", back_populates="contrato")


class Retirada(Base):
    __tablename__ = "retiradas"

    id_retirada = Column(Integer, primary_key=True, index=True)
    id_reserva = Column(Integer, ForeignKey("reservas.id_reserva"), unique=True, nullable=False)
    data_hora_retirada = Column(DateTime(timezone=True), server_default=func.now())
    obs_estado_entrega = Column(Text, nullable=True)
    foto_checkin = Column(String(255), nullable=True)

    reserva = relationship("Reserva", back_populates="retirada")


class Devolucao(Base):
    __tablename__ = "devolucoes"

    id_devolucao = Column(Integer, primary_key=True, index=True)
    id_reserva = Column(Integer, ForeignKey("reservas.id_reserva"), unique=True, nullable=False)
    data_hora_devolucao = Column(DateTime(timezone=True), server_default=func.now())
    obs_estado_retorno = Column(Text, nullable=True)
    foto_checkout = Column(String(255), nullable=True)

    reserva = relationship("Reserva", back_populates="devolucao")


class Avaliacao(Base):
    __tablename__ = "avaliacoes"

    id_avaliacao = Column(Integer, primary_key=True, index=True)
    id_reserva = Column(Integer, ForeignKey("reservas.id_reserva"), nullable=False)
    id_avaliador = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_avaliado = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    nota = Column(Integer, nullable=False)
    comentario = Column(Text, nullable=False)
    data_avaliacao = Column(DateTime(timezone=True), server_default=func.now())


class Denuncia(Base):
    __tablename__ = "denuncias"

    id_denuncia = Column(Integer, primary_key=True, index=True)
    id_reserva = Column(Integer, ForeignKey("reservas.id_reserva"), nullable=False)
    id_denunciante = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    motivo = Column(Text, nullable=False)
    descricao = Column(Text, nullable=False)
    foto_evidencia = Column(String(255), nullable=True)
    status_denuncia = Column(SAEnum(StatusDenuncia), default=StatusDenuncia.PENDENTE)
    resolucao = Column(Text, nullable=True)
    data_abertura = Column(DateTime(timezone=True), server_default=func.now())


class Mensagem(Base):
    __tablename__ = "mensagens"

    id_mensagem = Column(Integer, primary_key=True, index=True)
    id_reserva = Column(Integer, ForeignKey("reservas.id_reserva"), nullable=False)
    id_remetente = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    conteudo = Column(Text, nullable=False)
    data_envio = Column(DateTime(timezone=True), server_default=func.now())


class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id_log = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    acao = Column(String(100), nullable=False)
    detalhe = Column(Text, nullable=True)
    ip = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())