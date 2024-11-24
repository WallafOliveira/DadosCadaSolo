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
        # Tabela de usuários
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL
            )
        ''')
        # Tabela de dados do solo
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS solo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                ph REAL NOT NULL,
                umidade REAL NOT NULL,
                temperatura REAL NOT NULL,
                nitrogenio REAL NOT NULL,
                fosforo REAL NOT NULL,
                potassio REAL NOT NULL,
                microbioma REAL NOT NULL,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
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

# Endpoint para login do usuário
@app.route('/login', methods=['POST'])
def login_usuario():
    try:
        dados_login = request.get_json()
        email = dados_login['email']
        senha = dados_login['senha']

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Verificar se o email existe
            cursor.execute("SELECT id, senha FROM usuarios WHERE email = ?", (email,))
            resultado = cursor.fetchone()

            if resultado is None:
                return jsonify({'error': 'Usuário não encontrado'}), 404

            usuario_id, senha_armazenada = resultado['id'], resultado['senha']

            # Verificar a senha
            if not check_password_hash(senha_armazenada, senha):
                return jsonify({'error': 'Senha incorreta'}), 401

            return jsonify({'message': 'Login bem-sucedido!', 'usuario_id': usuario_id}), 200

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({'error': 'Erro inesperado no servidor'}), 500

# Endpoint para cadastrar dados do solo
@app.route('/api/solo', methods=['POST'])
def add_solo():
    try:
        data = request.get_json()
        usuario_id = data['usuario_id']  # ID do usuário que envia os dados
        valores = (
            usuario_id,
            data['ph'], 
            data['umidade'], 
            data['temperatura'], 
            data['nitrogenio'], 
            data['fosforo'], 
            data['potassio'], 
            data['microbioma']
        )

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(''' 
                INSERT INTO solo (usuario_id, ph, umidade, temperatura, nitrogenio, fosforo, potassio, microbioma)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', valores)
            conn.commit()

        return jsonify({"message": "Dados de solo inseridos com sucesso!"}), 201

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({'error': 'Erro ao inserir dados do solo'}), 500

# Endpoint para buscar condições anormais por usuário
@app.route('/api/condicoes_anormais/<int:usuario_id>', methods=['GET'])
def get_condicoes_anormais(usuario_id):
    faixa_ideal = {
        "ph": (6.0, 7.5),
        "umidade": (25, 40),
        "temperatura": (15, 30),
        "nitrogenio": (20, 50),
        "fosforo": (10, 30),
        "potassio": (15, 40),
        "microbioma": (4.5, 6.0)
    }

    tratamentos_recomendados = {
        "ph": "Adicionar calcário para aumentar o pH.",
        "umidade": "Irrigar a área para aumentar a umidade.",
        "temperatura": "Usar mulching para controlar a temperatura.",
        "nitrogenio": "Adicionar adubo nitrogenado.",
        "fosforo": "Adicionar fertilizantes fosfatados.",
        "potassio": "Adicionar fertilizantes ricos em potássio.",
        "microbioma": "Incorporar matéria orgânica ao solo."
    }

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Buscar dados de solo apenas do usuário especificado
            cursor.execute("SELECT * FROM solo WHERE usuario_id = ?", (usuario_id,))
            dados = [dict(row) for row in cursor.fetchall()]

        condicoes_anormais = []
        for row in dados:
            condicoes = {}
            for parametro, (min_ideal, max_ideal) in faixa_ideal.items():
                valor = row[parametro]
                if valor < min_ideal:
                    condicoes[parametro] = f"Baixo ({valor}). Ação: aumentar."
                elif valor > max_ideal:
                    condicoes[parametro] = f"Alto ({valor}). Ação: reduzir."
            if condicoes:
                condicoes_anormais.append({
                    "id": row["id"],
                    "condicoes": condicoes,
                    "tratamentos": {parametro: tratamentos_recomendados[parametro] for parametro in condicoes.keys()}
                })

        return jsonify(condicoes_anormais)

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({'error': 'Erro ao buscar condições anormais'}), 500

# Inicializar a aplicação
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

