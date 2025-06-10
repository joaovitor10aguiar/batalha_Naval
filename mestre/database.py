import sqlite3
from datetime import datetime

DB_NAME = "partida.db"

def conectar():
    return sqlite3.connect(DB_NAME)

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jogador (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partida (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jogador1_id INTEGER NOT NULL,
            jogador2_id INTEGER NOT NULL,
            vencedor_id INTEGER,
            turno_atual INTEGER NOT NULL,
            FOREIGN KEY(jogador1_id) REFERENCES jogador(id),
            FOREIGN KEY(jogador2_id) REFERENCES jogador(id),
            FOREIGN KEY(vencedor_id) REFERENCES jogador(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jogada (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partida_id INTEGER NOT NULL,
            jogador_id INTEGER NOT NULL,
            linha INTEGER NOT NULL,
            coluna INTEGER NOT NULL,
            ordem INTEGER NOT NULL,
            acerto BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(partida_id) REFERENCES partida(id),
            FOREIGN KEY(jogador_id) REFERENCES jogador(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS navio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jogador_id INTEGER NOT NULL,
            partida_id INTEGER NOT NULL,
            linha INTEGER NOT NULL,
            coluna INTEGER NOT NULL,
            atingido BOOLEAN DEFAULT 0,
            FOREIGN KEY(jogador_id) REFERENCES jogador(id),
            FOREIGN KEY(partida_id) REFERENCES partida(id)
        )
    ''')

    conn.commit()
    conn.close()

def login_ou_cadastrar_jogador(nome, usuario):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM jogador WHERE usuario = ?", (usuario,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]
    else:
        cursor.execute("INSERT INTO jogador (nome, usuario) VALUES (?, ?)", (nome, usuario))
        conn.commit()
        jogador_id = cursor.lastrowid
        conn.close()
        return jogador_id

def criar_partida(jogador1_id, jogador2_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO partida (jogador1_id, jogador2_id, turno_atual) VALUES (?, ?, ?)",
        (jogador1_id, jogador2_id, jogador1_id)
    )
    conn.commit()
    partida_id = cursor.lastrowid
    conn.close()
    return partida_id

def registrar_navios(jogador_id, partida_id, posicoes):
    conn = conectar()
    cursor = conn.cursor()
    for pos in posicoes:
        linha = pos["linha"]
        coluna = pos["coluna"]
        cursor.execute(
            "INSERT INTO navio (jogador_id, partida_id, linha, coluna) VALUES (?, ?, ?, ?)",
            (jogador_id, partida_id, linha, coluna)
        )
    conn.commit()
    conn.close()

def verificar_jogada_duplicada(partida_id, linha, coluna):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM jogada 
        WHERE partida_id = ? AND linha = ? AND coluna = ?
    """, (partida_id, linha, coluna))
    resultado = cursor.fetchone()[0]
    conn.close()
    return resultado > 0

def registrar_jogada(partida_id, jogador_id, linha, coluna, ordem):
    conn = conectar()
    cursor = conn.cursor()

    # Verifica turno atual
    cursor.execute("SELECT turno_atual FROM partida WHERE id = ?", (partida_id,))
    turno_atual = cursor.fetchone()[0]
    if turno_atual != jogador_id:
        conn.close()
        return {"erro": "Não é o turno desse jogador"}

    if verificar_jogada_duplicada(partida_id, linha, coluna):
        conn.close()
        return {"erro": "Esta posição já foi jogada. Escolha outra."}

    cursor.execute("SELECT jogador1_id, jogador2_id FROM partida WHERE id = ?", (partida_id,))
    p = cursor.fetchone()
    oponente_id = p[1] if jogador_id == p[0] else p[0]

    cursor.execute("""
        SELECT id FROM navio 
        WHERE partida_id = ? AND jogador_id = ? AND linha = ? AND coluna = ? AND atingido = 0
    """, (partida_id, oponente_id, linha, coluna))
    navio = cursor.fetchone()

    acerto = False
    if navio:
        acerto = True
        cursor.execute("UPDATE navio SET atingido = 1 WHERE id = ?", (navio[0],))

    cursor.execute("""
        INSERT INTO jogada (partida_id, jogador_id, linha, coluna, ordem, acerto)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (partida_id, jogador_id, linha, coluna, ordem, acerto))

    vitoria = verificar_vitoria(partida_id, oponente_id)
    if vitoria:
        atualizar_vencedor(partida_id, jogador_id)
        conn.commit()
        conn.close()
        return {"mensagem": f"Jogada registrada. Vitória do jogador {jogador_id}!", "acerto": acerto}

    conn.commit()
    conn.close()
    return {"mensagem": "Jogada registrada com sucesso.", "acerto": acerto}

def verificar_vitoria(partida_id, oponente_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM navio 
        WHERE partida_id = ? AND jogador_id = ? AND atingido = 0
    """, (partida_id, oponente_id))
    restante = cursor.fetchone()[0]
    conn.close()
    return restante == 0

def atualizar_vencedor(partida_id, vencedor_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE partida SET vencedor_id = ? WHERE id = ?", (vencedor_id, partida_id))
    conn.commit()
    conn.close()

def buscar_jogadas_por_partida(partida_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT jogador_id, linha, coluna, ordem, acerto, timestamp 
        FROM jogada 
        WHERE partida_id = ? 
        ORDER BY ordem ASC
    """, (partida_id,))
    jogadas = cursor.fetchall()
    conn.close()
    return [
        {
            "jogador_id": j[0],
            "linha": j[1],
            "coluna": j[2],
            "ordem": j[3],
            "acerto": bool(j[4]),
            "timestamp": j[5]
        }
        for j in jogadas
    ]
