from flask import Flask, render_template, request
import sqlite3
import uuid
import os
import requests

app = Flask(__name__)

# ==============================
# CONFIGURAÇÕES
# ==============================

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

# ==============================
# LISTA DE CONVIDADOS
# ==============================

CONVIDADOS_INICIAIS = [
    "Osmar",
    "Izolete",
    "Thiago",
    "Maurilio",
    "Lilian",
    "Iracema",
    "Reginaldo",
    "Marisete",
    "Meri",
    "Rudolfo",
    "Emanuelle",
    "Larissa Prates",
    "Larissa Brito",
    "Diogo",
    "Miguel",
    "Terezinha",
    "Renato",
    "Vitor",
    "Vilma",
    "Artur",
    "Sara",
    "Valmir",
    "Lucas",
    "Maria Eduarda",
    "Rafaella",
    "Kamilly",
    "Ana Laura",
    "Luiza",
    "Larissa Fermiano",
    "José Luiz",
    "Luiza Fermiano",
    "Luiza Beckhauser",
    "Denise",
    "Rafael",
    "Edna",
    "Kleiton",
    "Carol",
    "Caroline",
    "Giovana Kraisch",
    "Luiz Paulo",
    "Anne",
    "Daniely",
    "Bianca",
    "Lucineia",
    "Fernando",
    "Isabelli",
    "Patrick",
    "Celini",
    "Adriana Schulz",
    "Aldori",
    "Maria Clara",
    "Izabel",
    "Adriana Sedrez",
    "Marcelo",
    "Adriana Voigt",
    "Giovani",
    "Giovana",
    "Letícia",
    "Valcir",
    "Gabriel",
    "Susanny",
    "Kamilly",
    "Francisco",
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
            nome TEXT UNIQUE,
            confirmado INTEGER DEFAULT 0
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
            pass

    conn.commit()
    conn.close()

# ==============================
# DISCORD
# ==============================

def enviar_discord(nome):
    if not DISCORD_WEBHOOK:
        print("Webhook não configurado.")
        return

    data = {
        "content": f"🎉 **Nova confirmação!**\n\nConvidado: **{nome}**"
    }

    try:
        requests.post(DISCORD_WEBHOOK, json=data, timeout=5)
    except Exception as e:
        print("Erro ao enviar para Discord:", e)

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
                "SELECT id, nome, confirmado FROM convidados WHERE LOWER(nome) LIKE LOWER(?)",
                (nome_digitado + "%",)
            )

            resultados = cursor.fetchall()

            if len(resultados) == 1:
                convidado_id, nome_oficial, confirmado = resultados[0]

                if confirmado == 1:
                    conn.close()
                    return render_template(
                        "index.html",
                        erro="Presença já confirmada anteriormente."
                    )

                # marca como confirmado
                cursor.execute(
                    "UPDATE convidados SET confirmado = 1 WHERE id = ?",
                    (convidado_id,)
                )
                conn.commit()
                conn.close()

                enviar_discord(nome_oficial)

                return render_template(
                    "index.html",
                    sucesso="Presença confirmada com sucesso!"
                )

            elif len(resultados) > 1:
                conn.close()
                return render_template(
                    "index.html",
                    erro="Digite nome e sobrenome para confirmar."
                )

            else:
                conn.close()
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
