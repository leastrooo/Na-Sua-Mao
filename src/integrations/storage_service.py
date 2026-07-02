import os
import uuid
from PIL import Image
import io

UPLOAD_DIR = "static/uploads"
MAX_SIZE_KB = 500
MAX_DIMENSION = 1200 


def salvar_imagem(file_bytes: bytes, filename: str) -> str:
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    
    img = Image.open(io.BytesIO(file_bytes))

    
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    
    if max(img.size) > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    
    ext = ".jpg"
    nome_arquivo = f"{uuid.uuid4().hex}{ext}"
    caminho = os.path.join(UPLOAD_DIR, nome_arquivo)

    
    qualidade = 85
    while True:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=qualidade, optimize=True)
        tamanho_kb = buffer.tell() / 1024
        if tamanho_kb <= MAX_SIZE_KB or qualidade <= 30:
            break
        qualidade -= 10

    with open(caminho, "wb") as f:
        f.write(buffer.getvalue())

    return f"/{caminho}"
