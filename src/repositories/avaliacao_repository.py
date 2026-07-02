import sqlite3

DB_PATH = "nasuamao.db"


def criar_tabela():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluguel_id INTEGER NOT NULL,
            avaliador_id INTEGER NOT NULL,
            avaliado_id INTEGER NOT NULL,
            nota INTEGER NOT NULL,
            comentario TEXT
        )
    """)
    conn.commit()
    conn.close()


def salvar_avaliacao(aluguel_id, avaliador_id, avaliado_id, nota, comentario):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        INSERT INTO avaliacoes (aluguel_id, avaliador_id, avaliado_id, nota, comentario)
        VALUES (?, ?, ?, ?, ?)
    """, (aluguel_id, avaliador_id, avaliado_id, nota, comentario))
    conn.commit()
    avaliacao_id = cursor.lastrowid
    conn.close()
    return avaliacao_id


def buscar_avaliacoes_por_usuario(avaliado_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT id, aluguel_id, avaliador_id, avaliado_id, nota, comentario
        FROM avaliacoes WHERE avaliado_id = ?
    """, (avaliado_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
