from pydantic import BaseModel, Field
from typing import Optional


class AvaliacaoCreate(BaseModel):
    aluguel_id: int
    avaliador_id: int
    avaliado_id: int
    nota: int = Field(..., ge=1, le=5)
    comentario: Optional[str] = None


class AvaliacaoResponse(BaseModel):
    id: int
    aluguel_id: int
    avaliador_id: int
    avaliado_id: int
    nota: int
    comentario: Optional[str]

    class Config:
        from_attributes = True
      
