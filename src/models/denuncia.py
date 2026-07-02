from pydantic import BaseModel, Field
from typing import Optional


class DenunciaCreate(BaseModel):
    reserva_id: int
    denunciante_id: int
    motivo: str = Field(..., min_length=3)
    descricao: str = Field(..., min_length=10)
    foto_evidencia: Optional[str] = None


class DenunciaResolucao(BaseModel):
    resolucao: str = Field(..., min_length=10)


class DenunciaResponse(BaseModel):
    id_denuncia: int
    reserva_id: int
    denunciante_id: int
    motivo: str
    descricao: str
    foto_evidencia: Optional[str]
    status_denuncia: str
    resolucao: Optional[str]

    class Config:
        from_attributes = True