# app.py (Render + historique GPT)
from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime
import openai

app = Flask(__name__)

# === CONFIGURATION ===
BASE_PATH = os.path.join(os.getcwd(), "Hub_Personnel")
LOG_PATH = os.path.join(BASE_PATH, "GlitchOps/Sentinelle/logs")
MEMO_PATH = os.path.join(BASE_PATH, "GlitchOps/Sentinelle/memoire_agent.json")
COMMAND_PATH = os.path.join(BASE_PATH, "GlitchOps/Sentinelle/sentinelle.json")
HISTO_PATH = os.path.join(BASE_PATH, "GlitchOps/Sentinelle/historique_gpt.json")
openai.api_key = os.environ.get("OPENAI_API_KEY")

# === ROUTES ===
@app.route("/")
def dashboard():
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)

    logs = sorted(os.listdir(LOG_PATH), reverse=True)[:5] if os.path.exists(LOG_PATH) else []
    logs_display = []
    for log in logs:
        try:
            with open(os.path.join(LOG_PATH, log), 'r') as f:
                logs_display.append(f.read())
        except:
            continue

    last_update = logs_display[0].split("\n")[0] if logs_display else "Aucune activité."

    try:
        with open(MEMO_PATH, "r") as f:
            memoire = json.load(f)
    except Exception as e:
        print("❌ Erreur mémoire:", e)
        memoire = {}

    latest_result = None
    try:
        if os.path.exists(COMMAND_PATH):
            with open(COMMAND_PATH, "r") as f:
                cmd = json.load(f)
            if cmd.get("status") == "done" and "result" in cmd:
                latest_result = cmd["result"]
                # Ajout au fichier historique
                historique = []
                if os.path.exists(HISTO_PATH):
                    with open(HISTO_PATH, "r") as f:
                        historique = json.load(f)
                historique.insert(0, {
                    "timestamp": cmd.get("executed_at"),
                    "result": cmd["result"],
                    "type": cmd.get("type"),
                    "source": cmd.get("source")
                })
                with open(HISTO_PATH, "w") as f:
                    json.dump(historique[:25], f, indent=2)  # Garde les 25 derniers max
    except:
        latest_result = None

    historique_display = []
    try:
        if os.path.exists(HISTO_PATH):
            with open(HISTO_PATH, "r") as f:
                historique_display = json.load(f)
    except:
        historique_display = []

    return render_template("dashboard.html",
                           logs=logs_display,
                           last_update=last_update,
                           memoire_keys=list(memoire.keys()),
                           latest_result=latest_result,
                           historique=historique_display)

@app.route("/ping")
def ping():
    return jsonify({"status": "alive", "time": datetime.now().isoformat()})

@app.route("/gpt-command", methods=["POST"])
def gpt_command():
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


