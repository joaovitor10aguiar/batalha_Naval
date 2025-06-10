import sqlite3

conn = sqlite3.connect("partida.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM partida")
partidas = cursor.fetchall()

print("📌 Partidas registradas:")
for p in partidas:
    print(p)

print("\n📌 Partidas registradas:")
cursor.execute("SELECT id, jogador1_id, jogador2_id, turno_atual FROM partida ORDER BY id DESC")
for linha in cursor.fetchall():
    print(f"ID: {linha[0]}, Jogador1: {linha[1]}, Jogador2: {linha[2]}, Turno atual: {linha[3]}")

print("\n📌 Jogadas registradas:")
cursor.execute("SELECT partida_id, jogador_id, linha, coluna, acerto FROM jogada ORDER BY timestamp DESC LIMIT 10")
for jogada in cursor.fetchall():
    print(f"Partida {jogada[0]}, Jogador {jogada[1]}, Linha {jogada[2]}, Coluna {jogada[3]}, Acerto: {bool(jogada[4])}")

print("\n📌 Jogadores cadastrados:")
cursor.execute("SELECT * FROM jogador")
for jogador in cursor.fetchall():
    print(f"ID: {jogador[0]}, Nome: {jogador[1]}, Usuário: {jogador[2]}")

conn.close()
