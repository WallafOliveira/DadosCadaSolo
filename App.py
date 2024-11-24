from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_cors import CORS

app = Flask(__name__)

# Permitir apenas o domínio específico e garantir que o método OPTIONS e os cabeçalhos necessários sejam aceitos
CORS(app)


# Resto do código...

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
        conn.commit()



@app.route('/')
def home():
    return jsonify({"message": "API funcionando corretamente!"})

# Endpoint para cadastrar um novo usuário
@app.route('/usuarios', methods=['POST'])
def criar_usuario():
    try:
        novo_usuario = request.get_json()
        nome = novo_usuario['nome']
        email = novo_usuario['email']
        senha = novo_usuario['senha']  # A senha será recebida em texto simples

        # Gerar o hash da senha antes de salvar no banco de dados
        senha_hash = generate_password_hash(senha)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Inserir o usuário no banco de dados
            cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", 
                           (nome, email, senha_hash))
            conn.commit()

        return jsonify({"message": "Usuário criado com sucesso!"}), 201

    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email já está em uso'}), 409
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({'error': 'Erro inesperado no servidor'}), 500

# Endpoint para fazer login do usuário
@app.route('/login', methods=['POST'])
def login_usuario():
    try:
        dados_login = request.get_json()
        email = dados_login['email']
        senha = dados_login['senha']

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Verifica se o email existe
            cursor.execute("SELECT senha FROM usuarios WHERE email = ?", (email,))
            resultado = cursor.fetchone()

            if resultado is None:
                return jsonify({'error': 'Usuário não encontrado'}), 404

            senha_armazenada = resultado['senha']

            # Verifica se a senha fornecida é igual à armazenada no banco (comparação com hash)
            if not check_password_hash(senha_armazenada, senha):
                return jsonify({'error': 'Senha incorreta'}), 401

            return jsonify({'message': 'Login bem-sucedido!'}), 200

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({'error': 'Erro inesperado no servidor'}), 500

if __name__ == '__main__':
    # Inicializa o banco de dados antes de iniciar o servidor
    init_db()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

