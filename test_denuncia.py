import sys
import os
import pytest
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(__file__))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models.models import (
    Usuario, Ferramenta, Reserva, Denuncia, Categoria,
    StatusReserva, StatusDenuncia,
)
from src.repositories import denuncia_repository


@pytest.fixture(scope="function")
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def dados_base(db):
    categoria = Categoria(nome_categoria="Construção")
    db.add(categoria)
    db.flush()

    locador = Usuario(
        nome="Carlos Locador", email="carlos@teste.com", senha="hash",
        cpf="111.111.111-11", data_nascimento=date(1985, 3, 10), status_conta="ativo",
    )
    locatario = Usuario(
        nome="Maria Locataria", email="maria@teste.com", senha="hash",
        cpf="222.222.222-22", data_nascimento=date(1995, 7, 20), status_conta="ativo",
    )
    db.add_all([locador, locatario])
    db.flush()

    ferramenta = Ferramenta(
        id_locador=locador.id_usuario, id_categoria=categoria.id_categoria,
        titulo="Furadeira de Impacto", descricao="Furadeira profissional 750W",
        preco_diaria=Decimal("30.00"),
    )
    db.add(ferramenta)
    db.flush()

    reserva = Reserva(
        id_locatario=locatario.id_usuario, id_ferramenta=ferramenta.id_ferramenta,
        data_prevista_inicio=date.today(), data_prevista_fim=date.today() + timedelta(days=2),
        valor_total_calculado=Decimal("60.00"), status_reserva=StatusReserva.EM_USO,
    )
    db.add(reserva)
    db.commit()

    return {"locador": locador, "locatario": locatario, "ferramenta": ferramenta, "reserva": reserva}


class TestAbrirDenuncia:

    def test_criar_denuncia_com_sucesso(self, db, dados_base):
        reserva = dados_base["reserva"]
        locatario = dados_base["locatario"]

        denuncia = denuncia_repository.criar(
            db=db, reserva_id=reserva.id_reserva, denunciante_id=locatario.id_usuario,
            motivo="Item danificado", descricao="A furadeira foi devolvida com a broca quebrada.",
        )

        assert denuncia.id_denuncia is not None
        assert denuncia.motivo == "Item danificado"
        assert denuncia.status_denuncia == StatusDenuncia.PENDENTE

    def test_abrir_denuncia_altera_status_reserva_para_em_disputa(self, db, dados_base):
        reserva = dados_base["reserva"]
        locatario = dados_base["locatario"]

        denuncia_repository.criar(
            db=db, reserva_id=reserva.id_reserva, denunciante_id=locatario.id_usuario,
            motivo="Comportamento inadequado", descricao="O locador foi grosseiro durante a retirada.",
        )

        db.refresh(reserva)
        assert reserva.status_reserva == StatusReserva.EM_DISPUTA

    def test_denuncia_com_foto_evidencia(self, db, dados_base):
        reserva = dados_base["reserva"]
        locatario = dados_base["locatario"]

        denuncia = denuncia_repository.criar(
            db=db, reserva_id=reserva.id_reserva, denunciante_id=locatario.id_usuario,
            motivo="Atraso na devolução", descricao="A ferramenta não foi devolvida no prazo.",
            foto_evidencia="evidencia_abc123.jpg",
        )

        assert denuncia.foto_evidencia == "evidencia_abc123.jpg"

    def test_denuncia_sem_foto_e_valida(self, db, dados_base):
        reserva = dados_base["reserva"]
        locatario = dados_base["locatario"]

        denuncia = denuncia_repository.criar(
            db=db, reserva_id=reserva.id_reserva, denunciante_id=locatario.id_usuario,
            motivo="Item diferente do anunciado", descricao="A ferramenta entregue não era a mesma da foto.",
        )

        assert denuncia.foto_evidencia is None
        assert denuncia.id_denuncia is not None

    def test_buscar_denuncia_por_reserva(self, db, dados_base):
        reserva = dados_base["reserva"]
        locatario = dados_base["locatario"]

        denuncia_repository.criar(
            db=db, reserva_id=reserva.id_reserva, denunciante_id=locatario.id_usuario,
            motivo="Teste busca", descricao="Descrição de teste.",
        )

        encontrada = denuncia_repository.buscar_por_reserva(db, reserva.id_reserva)
        assert encontrada is not None
        assert encontrada.motivo == "Teste busca"

    def test_buscar_denuncia_inexistente_retorna_none(self, db):
        resultado = denuncia_repository.buscar_por_reserva(db, reserva_id=9999)
        assert resultado is None


class TestTratarDenuncia:

    def _criar_denuncia(self, db, dados_base):
        reserva = dados_base["reserva"]
        locatario = dados_base["locatario"]
        return denuncia_repository.criar(
            db=db, reserva_id=reserva.id_reserva, denunciante_id=locatario.id_usuario,
            motivo="Ferramenta danificada", descricao="Detalhe do problema relatado.",
        )

    def test_resolver_denuncia_com_sucesso(self, db, dados_base):
        denuncia = self._criar_denuncia(db, dados_base)

        resolvida = denuncia_repository.resolver(
            db=db, denuncia_id=denuncia.id_denuncia,
            resolucao="Advertência enviada ao locatário. Caso encerrado.",
        )

        assert resolvida is not None
        assert resolvida.status_denuncia == StatusDenuncia.RESOLVIDA
        assert "Advertência" in resolvida.resolucao

    def test_resolver_denuncia_atualiza_status_reserva(self, db, dados_base):
        reserva = dados_base["reserva"]
        denuncia = self._criar_denuncia(db, dados_base)

        denuncia_repository.resolver(
            db=db, denuncia_id=denuncia.id_denuncia,
            resolucao="Situação resolvida entre as partes.",
        )

        db.refresh(reserva)
        assert reserva.status_reserva == StatusReserva.FINALIZADO

    def test_resolver_denuncia_inexistente_retorna_none(self, db):
        resultado = denuncia_repository.resolver(db, denuncia_id=9999, resolucao="Teste")
        assert resultado is None

    def test_listar_denuncias_pendentes(self, db, dados_base):
        reserva = dados_base["reserva"]
        locatario = dados_base["locatario"]

        denuncia_repository.criar(
            db=db, reserva_id=reserva.id_reserva, denunciante_id=locatario.id_usuario,
            motivo="Problema 1", descricao="Descrição 1",
        )

        pendentes = denuncia_repository.listar_pendentes(db)
        assert len(pendentes) == 1
        assert pendentes[0].status_denuncia == StatusDenuncia.PENDENTE

    def test_denuncia_resolvida_nao_aparece_na_lista_de_pendentes(self, db, dados_base):
        reserva = dados_base["reserva"]
        locatario = dados_base["locatario"]

        denuncia = denuncia_repository.criar(
            db=db, reserva_id=reserva.id_reserva, denunciante_id=locatario.id_usuario,
            motivo="Problema resolvível", descricao="Descrição detalhada.",
        )

        denuncia_repository.resolver(
            db=db, denuncia_id=denuncia.id_denuncia,
            resolucao="Resolvido com sucesso.",
        )

        pendentes = denuncia_repository.listar_pendentes(db)
        assert len(pendentes) == 0

    def test_buscar_denuncia_por_id(self, db, dados_base):
        reserva = dados_base["reserva"]
        locatario = dados_base["locatario"]

        criada = denuncia_repository.criar(
            db=db, reserva_id=reserva.id_reserva, denunciante_id=locatario.id_usuario,
            motivo="Busca por ID", descricao="Teste de busca direta.",
        )

        encontrada = denuncia_repository.buscar_por_id(db, criada.id_denuncia)
        assert encontrada is not None
        assert encontrada.id_denuncia == criada.id_denuncia