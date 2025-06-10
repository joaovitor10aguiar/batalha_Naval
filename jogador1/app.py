from flask import Flask, request, render_template, redirect, url_for
from flask_socketio import SocketIO
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

BASE_URL = "http://localhost:5000"

jogadores = {}
navios_posicionados = {}

@app.route('/', methods=['POST'])
def receber_jogada():
    dados = request.get_json()
    socketio.emit('atualizar_tabuleiro', {
        "linha": dados['linha'],
        "coluna": dados['coluna'],
        "resultado": "acertou" if [dados['linha'], dados['coluna']] in navios_posicionados.get(dados['player'], []) else "errou"
    })
    socketio.emit('mensagem', f"Jogador {dados['player']} jogou em ({dados['linha']}, {dados['coluna']})")
    return {"mensagem": "Jogada recebida", "resultado": "acertou" if [dados['linha'], dados['coluna']] in navios_posicionados.get(dados['player'], []) else "errou"}

@app.route('/registro', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        nome = request.form.get("nome")
        usuario = request.form.get("usuario")

        try:
            response = requests.post(f"{BASE_URL}/login", json={"nome": nome, "usuario": usuario})
            response.raise_for_status()
            data = response.json()
            jogador_id = data.get("jogador_id")
            if not jogador_id:
                return "Erro: resposta do servidor não contém jogador_id", 500

            return redirect(url_for("posicionar", jogador_id=jogador_id))

        except Exception as e:
            return f"Erro durante o registro: {e}", 500

    return render_template('registro.html')

@app.route('/posicionar/<int:jogador_id>')
def posicionar(jogador_id):
    return render_template('posicionar.html', jogador_id=jogador_id)

@app.route('/registrar_navios', methods=['POST'])
def registrar_navios():
    dados = request.get_json()
    navios_posicionados[dados['jogador_id']] = dados['posicoes']
    return {"mensagem": "Navios registrados com sucesso!"}

@app.route('/jogo/<int:jogador_id>/<int:partida_id>')
def jogo(jogador_id, partida_id):
    return render_template('jogo.html', jogador_id=jogador_id, partida_id=partida_id)

if __name__ == '__main__':
    socketio.run(app, port=5001, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0')
