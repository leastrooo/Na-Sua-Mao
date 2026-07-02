from sqlalchemy.orm import Session
from models.models import Ferramenta, StatusFerramenta, Categoria
from math import radians, sin, cos, sqrt, atan2

LIMITE_FERRAMENTAS_ATIVAS = 10 

def obter_ou_criar_categoria(db: Session, nome_categoria: str) -> int:
    
    categoria = db.query(Categoria).filter(Categoria.nome_categoria == nome_categoria).first()
    if not categoria:
        categoria = Categoria(nome_categoria=nome_categoria)
        db.add(categoria)
        db.commit()
        db.refresh(categoria)
    return categoria.id_categoria

def cadastrar_ferramenta(db: Session, dados: dict, locador_id: int) -> dict:
    if not dados.get("categoria"):
        return {"erro": "A categoria é obrigatória."}

    
    id_cat = obter_ou_criar_categoria(db, dados["categoria"])

    qtd_ativas = db.query(Ferramenta).filter(
        Ferramenta.id_locador == locador_id,
        Ferramenta.status_ferramenta == StatusFerramenta.DISPONIVEL
    ).count()
    
    if qtd_ativas >= LIMITE_FERRAMENTAS_ATIVAS:
        return {"erro": f"Limite de {LIMITE_FERRAMENTAS_ATIVAS} ferramentas disponíveis atingido."}

    ferramenta = Ferramenta(
        titulo=dados["nome"], 
        descricao=dados["descricao"],
        id_categoria=id_cat, 
        preco_diaria=float(dados["valor_diaria"]),
        id_locador=locador_id,
        foto1=dados.get("foto1"),
        foto2=dados.get("foto2"),
        foto3=dados.get("foto3"),
        foto4=dados.get("foto4"),
        foto5=dados.get("foto5"),
        status_ferramenta=StatusFerramenta.DISPONIVEL
    )
    db.add(ferramenta)
    db.commit()
    db.refresh(ferramenta)
    return {"ferramenta": ferramenta}

def calcular_distancia(coord1, coord2):
    
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return 6371 * c 

def buscar_ferramentas(db: Session, busca: str = None, categoria_nome: str = None, distancia_max: float = 5.0, user_coord: tuple = None):
    query = db.query(Ferramenta).filter(Ferramenta.status_ferramenta == StatusFerramenta.DISPONIVEL)
    
    if busca:
        query = query.filter(Ferramenta.titulo.ilike(f"%{busca}%"))
    if categoria_nome:
        query = query.join(Categoria).filter(Categoria.nome_categoria == categoria_nome)
        
    ferramentas = query.all()
    
    
    if user_coord and distancia_max:
        return [f for f in ferramentas if calcular_distancia(user_coord, (f.locador.latitude, f.locador.longitude)) <= distancia_max]
    
    return ferramentas

def atualizar_status_ferramenta(db: Session, ferramenta_id: int, novo_status: StatusFerramenta):
    ferramenta = db.query(Ferramenta).filter(Ferramenta.id_ferramenta == ferramenta_id).first()
    if ferramenta:
        ferramenta.status_ferramenta = novo_status
        db.commit()
