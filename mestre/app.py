from flask import Flask, request, jsonify
from flask_socketio import SocketIO
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
socketio = SocketIO(app, cors_allowed_origins="*")

turnos = {}

# Criação das tabelas ao iniciar
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
    turnos[partida_id] = jogador1_id
    return jsonify({"partida_id": partida_id})

@app.route("/registrar_navios", methods=["POST"])
def registrar_navios_rota():
    dados = request.get_json()
    jogador_id = dados["jogador_id"]
    partida_id = dados["partida_id"]
    posicoes = dados["posicoes"]  # lista de pares [linha, coluna]
    registrar_navios(jogador_id, partida_id, posicoes)
    return jsonify({"mensagem": "Navios posicionados com sucesso"})

def verificar_turno(partida_id, jogador_id, turnos):
    return turnos.get(partida_id) == jogador_id

def alternar_turno(partida_id, jogador1_id, jogador2_id):
    atual = turnos.get(partida_id)
    turnos[partida_id] = jogador2_id if atual == jogador1_id else jogador1_id

@app.route("/jogada", methods=["POST"])
def jogada():
    dados = request.get_json()
    partida_id = dados["partida_id"]
    jogador_id = dados["jogador_id"]
    linha = dados["linha"]
    coluna = dados["coluna"]
    ordem = dados["ordem"]

    # Verificar turno
    if not verificar_turno(partida_id, jogador_id, turnos):
        return jsonify({"erro": "Não é o turno desse jogador"}), 403

    resultado = registrar_jogada(partida_id, jogador_id, linha, coluna, ordem)

    # Alternar turno apenas se a jogada for válida
    if "erro" not in resultado:
        # Buscar os jogadores para alternar corretamente
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT jogador1_id, jogador2_id FROM partida WHERE id = ?", (partida_id,))
        jogador1_id, jogador2_id = cursor.fetchone()
        conn.close()

        alternar_turno(partida_id, jogador1_id, jogador2_id)

        socketio.emit("nova_jogada", {
            "partida_id": partida_id,
            "jogador_id": jogador_id,
            "linha": linha,
            "coluna": coluna,
            "ordem": ordem,
            "acerto": resultado.get("acerto", False)
        })

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
        turnos[partida_id] = turno
    conn.close()

carregar_turnos()

if __name__ == "__main__":
    socketio.run(app, debug=True)
