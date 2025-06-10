from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import sqlite3
from database import conectar
from database import (
    criar_tabelas,
    login_ou_cadastrar_jogador,
    criar_partida,
    registrar_jogada,
    buscar_jogadas_por_partida,
    registrar_navios
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002"
]}})
socketio = SocketIO(app, cors_allowed_origins=[
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002"
])

turnos = {}

criar_tabelas()

@app.route("/login", methods=["POST"])
def login():
    dados = request.get_json()
    nome = dados.get("nome")
    usuario = dados.get("usuario")
    jogador_id = login_ou_cadastrar_jogador(nome, usuario)
    return jsonify({"jogador_id": jogador_id})

@app.route("/nova_partida", methods=["POST"])
def nova_partida():
    dados = request.get_json()
    jogador1_id = dados.get("jogador1_id")
    jogador2_id = dados.get("jogador2_id")
    partida_id = criar_partida(jogador1_id, jogador2_id)

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE partida SET turno_atual = ? WHERE id = ?", (jogador1_id, partida_id))
    conn.commit()
    conn.close()

    turnos[partida_id] = jogador1_id
    print(f"[DEBUG] Partida {partida_id} iniciada. Primeiro turno: Jogador {jogador1_id}")

    # Emitir notificação para ambos os jogadores que a partida iniciou
    socketio.emit("jogador_pronto", {
        "partida_id": partida_id,
        "jogador1_id": jogador1_id,
        "jogador2_id": jogador2_id,
        "turno": jogador1_id
    })

    return jsonify({"partida_id": partida_id})

@app.route("/registrar_navios", methods=["POST"])
def registrar_navios_rota():
    dados = request.get_json()
    jogador_id = dados["jogador_id"]
    partida_id = dados["partida_id"]
    posicoes = dados["posicoes"]
    registrar_navios(jogador_id, partida_id, posicoes)
    return jsonify({"mensagem": "Navios posicionados com sucesso"})

def verificar_turno(partida_id, jogador_id):
    return turnos.get(partida_id) == jogador_id

def alternar_turno(partida_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT jogador1_id, jogador2_id, turno_atual FROM partida WHERE id = ?", (partida_id,))
    partida = cursor.fetchone()
    if not partida:
        conn.close()
        return
    novo_turno = partida[1] if partida[2] == partida[0] else partida[0]
    cursor.execute("UPDATE partida SET turno_atual = ? WHERE id = ?", (novo_turno, partida_id))
    conn.commit()
    conn.close()
    turnos[partida_id] = novo_turno

@app.route("/jogada", methods=["POST"])
def jogada():
    dados = request.get_json()
    partida_id = dados["partida_id"]
    jogador_id = dados["jogador_id"]
    linha = dados["linha"]
    coluna = dados["coluna"]
    ordem = dados.get("ordem", 1)

    if not verificar_turno(partida_id, jogador_id):
        return jsonify({"erro": "Não é o turno desse jogador"}), 403

    resultado = registrar_jogada(partida_id, jogador_id, linha, coluna, ordem)

    if "erro" not in resultado:
        alternar_turno(partida_id)
        socketio.emit("atualizar_tabuleiro", {
            "linha": linha,
            "coluna": coluna,
            "resultado": "acertou" if resultado.get("acerto") else "errou"
        })
        socketio.emit("mensagem", resultado["mensagem"])

    return jsonify(resultado)

@app.route("/jogadas/<int:partida_id>", methods=["GET"])
def listar_jogadas(partida_id):
    jogadas = buscar_jogadas_por_partida(partida_id)
    return jsonify(jogadas)

def carregar_turnos():
    conn = sqlite3.connect("partida.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, turno_atual FROM partida")
    for partida_id, turno in cursor.fetchall():
        if turno:
            turnos[partida_id] = turno
    conn.close()

carregar_turnos()

if __name__ == "__main__":
    carregar_turnos()
    print(f"[DEBUG] Turnos carregados do banco: {turnos}")
    socketio.run(app, debug=True)
