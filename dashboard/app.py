from flask import Flask, render_template, jsonify, request
import subprocess

app = Flask(__name__)

# ---------------- PATHS ----------------
BASE_SQUID = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/squid_status"

START_SQUID = f"{BASE_SQUID}/start_squid.sh"
STOP_SQUID = f"{BASE_SQUID}/stop_squid.sh"
RESTART_SQUID = f"{BASE_SQUID}/restart_squid.sh"
RELOAD_SQUID = f"{BASE_SQUID}/reload_squid.sh"

BLOCK_SCRIPT = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/actions/block_site.sh"
UNBLOCK_SCRIPT = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/actions/unblock_site.sh"
CLEAR_SCRIPT = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/actions/reset_lists.sh"

BLOCK_FILE = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/blocked_sites.txt"

LOGS = []


def run(cmd):
    """Run system command and capture output"""
    result = subprocess.run(cmd, capture_output=True, text=True)

    out = result.stdout.strip()
    err = result.stderr.strip()

    if out:
        LOGS.append(out)
    if err:
        LOGS.append("ERROR: " + err)

    return out, err


# ---------------- DASHBOARD ----------------
@app.route("/")
def home():
    return render_template("dashboard.html")


# ---------------- SQUID CONTROL ----------------
@app.route("/squid/start", methods=["POST"])
def start():
    out, err = run(["bash", START_SQUID])
    return {"output": out, "error": err}


@app.route("/squid/stop", methods=["POST"])
def stop():
    out, err = run(["bash", STOP_SQUID])
    return {"output": out, "error": err}


@app.route("/squid/restart", methods=["POST"])
def restart():
    out, err = run(["bash", RESTART_SQUID])
    return {"output": out, "error": err}


@app.route("/squid/reload", methods=["POST"])
def reload():
    out, err = run(["bash", RELOAD_SQUID])
    return {"output": out, "error": err}


# ---------------- BLOCK ----------------
@app.route("/block", methods=["POST"])
def block():
    site = request.json["site"]
    out, err = run(["bash", BLOCK_SCRIPT, site])
    return {"output": out, "error": err}


@app.route("/unblock", methods=["POST"])
def unblock():
    site = request.json["site"]
    out, err = run(["bash", UNBLOCK_SCRIPT, site])
    return {"output": out, "error": err}

@app.route("/clear", methods=["POST"])
def clear():
    result = subprocess.run(
        ["bash", CLEAR_SCRIPT],
        capture_output=True,
        text=True
    )

    return {
        "output": result.stdout,
        "error": result.stderr
    }
    
# ---------------- LIST ----------------
@app.route("/lists")
def lists():
    try:
        with open(BLOCK_FILE) as f:
            blocked = [x.strip() for x in f.readlines() if x.strip()]
    except:
        blocked = []

    return jsonify({"blocked": blocked})


# ---------------- LOGS ----------------
@app.route("/logs")
def logs():
    return jsonify({"logs": LOGS})


 # ---------------- REFRESH STATUS ----------------
@app.route("/squid/status")
def squid_status():
    result = subprocess.run(
        ["systemctl", "is-active", "squid"],
        capture_output=True,
        text=True
    )

    status = result.stdout.strip()

    if status == "active":
        state = "active"
    elif status == "inactive":
        state = "inactive"
    else:
        state = "unknown"

    return jsonify({"status": state})


if __name__ == "__main__":
    app.run(debug=True)