from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Caminho para o banco de dados SQLite
db_path = "meu_banco.db"

# Função para criar a conexão com o banco de dados
def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Para acessar os resultados como dicionários
    return conn

# Função para inicializar o banco de dados
def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL
            )
        ''')
        
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS solo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ph REAL,
                umidade REAL,
                temperatura REAL,
                nitrogenio REAL,
                fosforo REAL,
                potassio REAL,
                microbioma REAL,
                usuario_id INTEGER,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')

        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS condicoes_anormais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                solo_id INTEGER,
                parametro TEXT NOT NULL,
                condicao TEXT NOT NULL,
                acao TEXT NOT NULL,
                FOREIGN KEY (solo_id) REFERENCES solo (id)
            )
        ''')
        conn.commit()

# Endpoint para cadastrar um novo usuário
@app.route('/usuarios', methods=['POST'])
def criar_usuario():
    try:
        novo_usuario = request.get_json()
        nome = novo_usuario['nome']
        email = novo_usuario['email']
        senha = novo_usuario['senha']

        senha_hash = generate_password_hash(senha)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", 
                           (nome, email, senha_hash))
            conn.commit()

        return jsonify({"message": "Usuário criado com sucesso!"}), 201

    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email já está em uso'}), 409
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({'error': 'Erro inesperado no servidor'}), 500

# Endpoint para login de usuário
@app.route('/login', methods=['POST'])
def login_usuario():
    try:
        dados_login = request.get_json()
        email = dados_login['email']
        senha = dados_login['senha']

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT senha, id FROM usuarios WHERE email = ?", (email,))
            resultado = cursor.fetchone()

            if resultado is None:
                return jsonify({'error': 'Usuário não encontrado'}), 404

            senha_armazenada = resultado['senha']

            if not check_password_hash(senha_armazenada, senha):
                return jsonify({'error': 'Senha incorreta'}), 401

            return jsonify({'message': 'Login bem-sucedido!', 'usuario_id': resultado['id']}), 200

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({'error': 'Erro inesperado no servidor'}), 500

# Endpoint para cadastrar dados do solo (relacionados ao usuário)
@app.route('/api/solo', methods=['POST'])
def add_solo():
    try:
        dados_solo = request.get_json()
        usuario_id = dados_solo['usuario_id']
        ph = dados_solo['ph']
        umidade = dados_solo['umidade']
        temperatura = dados_solo['temperatura']
        nitrogenio = dados_solo['nitrogenio']
        fosforo = dados_solo['fosforo']
        potassio = dados_solo['potassio']
        microbioma = dados_solo['microbioma']

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(''' 
                INSERT INTO solo (ph, umidade, temperatura, nitrogenio, fosforo, potassio, microbioma, usuario_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ph, umidade, temperatura, nitrogenio, fosforo, potassio, microbioma, usuario_id))
            conn.commit()

        return jsonify({"message": "Dados do solo inseridos com sucesso!"}), 201

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({'error': 'Erro ao inserir dados do solo'}), 500

# Endpoint para registrar as condições anormais do solo
@app.route('/api/condicoes_anormais', methods=['POST'])
def add_condicoes_anormais():
    try:
        condicoes = request.get_json()
        solo_id = condicoes['solo_id']
        parametro = condicoes['parametro']
        condicao = condicoes['condicao']
        acao = condicoes['acao']

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(''' 
                INSERT INTO condicoes_anormais (solo_id, parametro, condicao, acao)
                VALUES (?, ?, ?, ?)
            ''', (solo_id, parametro, condicao, acao))
            conn.commit()

        return jsonify({"message": "Condição anormal registrada com sucesso!"}), 201

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({'error': 'Erro ao registrar condição anormal'}), 500

# Inicializar a aplicação
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
