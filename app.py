# app.py (interface Flask robuste + cœur JSON partagé)
from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime

try:
    import openai
except ImportError:
    openai = None

app = Flask(__name__)

# === CONFIGURATION ===
BASE_PATH = os.path.join(os.getcwd(), "Hub_Personnel")
LOG_PATH = os.path.join(BASE_PATH, "GlitchOps/Sentinelle/logs")
MEMO_PATH = os.path.join(BASE_PATH, "GlitchOps/Sentinelle/memoire_agent.json")
COMMAND_PATH = os.path.join(BASE_PATH, "GlitchOps/Sentinelle/sentinelle.json")

if openai:
    openai.api_key = os.environ.get("OPENAI_API_KEY")  # Clé stockée en variable d'env

# === ROUTES ===
@app.route("/")
def dashboard():
    try:
        os.makedirs(LOG_PATH, exist_ok=True)
        logs = sorted(os.listdir(LOG_PATH), reverse=True)[:5]
        logs_display = []
        for log in logs:
            with open(os.path.join(LOG_PATH, log), 'r') as f:
                logs_display.append(f.read())

        last_update = logs_display[0].split("\n")[0] if logs_display else "Aucune activité."
        memoire = json.load(open(MEMO_PATH)) if os.path.exists(MEMO_PATH) else {}

        return render_template("dashboard.html",
                               logs=logs_display,
                               last_update=last_update,
                               memoire_keys=list(memoire.keys()))
    except Exception as e:
        return f"Erreur lors du chargement du tableau de bord : {str(e)}", 500

@app.route("/ping")
def ping():
    return jsonify({"status": "alive", "time": datetime.now().isoformat()})

@app.route("/gpt-command", methods=["POST"])
def gpt_command():
    if not openai:
        return jsonify({"error": "Le module openai n'est pas installé."}), 500
    if not openai.api_key:
        return jsonify({"error": "Clé API GPT manquante."}), 500

    data = request.json
    command_type = data.get("type")
    params = data.get("params", {})

    if command_type == "generate_summary":
        content = "Résumé demandé: " + json.dumps(params)
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Tu es une IA de synthèse."},
                    {"role": "user", "content": content}
                ]
            )
            summary = response["choices"][0]["message"]["content"]
            return jsonify({"summary": summary})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Commande inconnue."}), 400

@app.route("/api/command", methods=["POST"])
def api_command():
    data = request.json
    payload = {
        "type": data.get("type"),
        "params": data.get("params", {}),
        "status": "pending",
        "source": "web",
        "timestamp": datetime.now().isoformat()
    }
    try:
        os.makedirs(os.path.dirname(COMMAND_PATH), exist_ok=True)
        with open(COMMAND_PATH, "w") as f:
            json.dump(payload, f, indent=2)
        return jsonify({"status": "enregistré", "path": COMMAND_PATH})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === LANCEMENT ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


