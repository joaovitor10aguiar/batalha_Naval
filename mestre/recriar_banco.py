import os
import sqlite3

DB_NAME = "partida.db"

def recriar_banco():
    # Apaga o arquivo do banco se ele existir
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("🧹 Banco de dados antigo removido.")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Criação das tabelas
    cursor.execute('''
        CREATE TABLE jogador (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE partida (
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
        CREATE TABLE jogada (
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
        CREATE TABLE navio (
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
    print("✅ Banco de dados recriado com sucesso!")

if __name__ == "__main__":
    recriar_banco()
