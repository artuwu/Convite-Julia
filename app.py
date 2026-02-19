from flask import Flask, render_template, request
import sqlite3
import uuid
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)

# ==============================
# CONFIGURAÇÕES
# ==============================

SEU_EMAIL = os.environ.get("EMAIL_USER")
SENHA_EMAIL = os.environ.get("EMAIL_PASS")

# Caminho seguro para o banco no Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

# ==============================
# LISTA DE CONVIDADOS
# ==============================

CONVIDADOS_INICIAIS = [
    "Artur Mendes",
    "Julia Souza",
    "Carlos Silva",
]

# ==============================
# BANCO DE DADOS
# ==============================

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS convidados (
            id TEXT PRIMARY KEY,
            nome TEXT UNIQUE
        )
    """)

    conn.commit()
    conn.close()

def cadastrar_convidados_iniciais():
    conn = get_connection()
    cursor = conn.cursor()

    for nome in CONVIDADOS_INICIAIS:
        try:
            cursor.execute(
                "INSERT INTO convidados (id, nome) VALUES (?, ?)",
                (str(uuid.uuid4()), nome)
            )
        except sqlite3.IntegrityError:
            pass  # já existe

    conn.commit()
    conn.close()

# ==============================
# EMAIL
# ==============================

def enviar_email(nome):
    # Só tenta enviar se variáveis existirem
    if not SEU_EMAIL or not SENHA_EMAIL:
        print("Email não configurado.")
        return

    corpo = f"""
Nova confirmação!

Convidado confirmado: {nome}
"""

    msg = MIMEText(corpo)
    msg["Subject"] = "Nova confirmação - Festa 18"
    msg["From"] = SEU_EMAIL
    msg["To"] = SEU_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(SEU_EMAIL, SENHA_EMAIL)
            server.send_message(msg)
    except Exception as e:
        print("Erro ao enviar email:", e)

# ==============================
# ROTA PRINCIPAL
# ==============================

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            nome_digitado = request.form["nome"].strip()

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT nome FROM convidados WHERE LOWER(nome) LIKE LOWER(?)",
                (nome_digitado + "%",)
            )

            resultados = cursor.fetchall()
            conn.close()

            if len(resultados) == 1:
                nome_oficial = resultados[0][0]
                enviar_email(nome_oficial)
                return render_template(
                    "index.html",
                    sucesso="Presença confirmada com sucesso!"
                )

            elif len(resultados) > 1:
                return render_template(
                    "index.html",
                    erro="Digite nome e sobrenome para confirmar."
                )

            else:
                return render_template(
                    "index.html",
                    erro="Seu nome não está na lista de convidados."
                )

        except Exception as e:
            print("Erro no POST:", e)
            return render_template(
                "index.html",
                erro="Ocorreu um erro. Tente novamente."
            )

    return render_template("index.html")

# ==============================
# INICIALIZAÇÃO
# ==============================

init_db()
cadastrar_convidados_iniciais()

# ==============================
# START LOCAL
# ==============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
