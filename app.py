# app.py (interface Flask minimale iPhone friendly)
from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)

# === CONFIGURATION ===
BASE_PATH = "/data/Hub_Personnel"
LOG_PATH = os.path.join(BASE_PATH, "GlitchOps/Sentinelle/logs")
MEMO_PATH = os.path.join(BASE_PATH, "GlitchOps/Sentinelle/memoire_agent.json")

# === ROUTES ===
@app.route("/")
def dashboard():
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)
    
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

@app.route("/ping")
def ping():
    return jsonify({"status": "alive", "time": datetime.now().isoformat()})

# === LANCEMENT ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
