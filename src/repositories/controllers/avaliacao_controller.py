from fastapi import APIRouter, HTTPException
from src.models.avaliacao import AvaliacaoCreate
from src.repositories import avaliacao_repository

router = APIRouter(prefix="/avaliacoes", tags=["Avaliações"])

avaliacao_repository.criar_tabela()


@router.post("/", response_model=dict)
def criar_avaliacao(avaliacao: AvaliacaoCreate):
    if avaliacao.nota < 1 or avaliacao.nota > 5:
        raise HTTPException(status_code=400, detail="Nota deve ser entre 1 e 5")

    avaliacao_id = avaliacao_repository.salvar_avaliacao(
        avaliacao.aluguel_id,
        avaliacao.avaliador_id,
        avaliacao.avaliado_id,
        avaliacao.nota,
        avaliacao.comentario
    )
    return {"mensagem": "Avaliação criada com sucesso!", "id": avaliacao_id}


@router.get("/usuario/{avaliado_id}")
def listar_avaliacoes(avaliado_id: int):
    rows = avaliacao_repository.buscar_avaliacoes_por_usuario(avaliado_id)
    return [
        {
            "id": r[0],
            "aluguel_id": r[1],
            "avaliador_id": r[2],
            "avaliado_id": r[3],
            "nota": r[4],
            "comentario": r[5]
        }
        for r in rows
    ]
