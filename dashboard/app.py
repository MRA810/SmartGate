from flask import Flask, render_template, jsonify, request
import subprocess
from squid_parser import parse_squid_logs

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
LOG_FILE = "/var/log/squid/access.log"
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

# ---------------- clear_log ----------------
import subprocess
from flask import jsonify

@app.route("/squid/clear-log", methods=["POST"])
def clear_log():
    try:
        subprocess.run(
            ["sudo", "truncate", "-s", "0", "/var/log/squid/access.log"],
            check=True
        )
        return jsonify({"output": "Log cleared"})
    except Exception as e:
        return jsonify({"error": str(e)})


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


# ---------------- CLEAR CACHE ----------------
@app.route("/squid/clear-cache", methods=["POST"])
def clear_cache():
    try:
        subprocess.run(["sudo", "systemctl", "stop", "squid"], check=True)

        subprocess.run(["sudo", "rm", "-rf", "/var/spool/squid/*"], check=True)

        subprocess.run(["sudo", "rm", "-rf", "/var/spool/squid/00/*"], check=False)

        subprocess.run(["sudo", "squid", "-z"], check=True)

        subprocess.run(["sudo", "systemctl", "start", "squid"], check=True)

        return jsonify({"output": "Cache cleared successfully"})

    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------- CRON LOG ----------------
@app.route("/squid/cron-log")
def cron_log():
    try:
        with open("/var/log/squid/cron.log", "r") as f:
            lines = f.readlines()

        return jsonify({"last": lines[-1] if lines else ""})
    except Exception as e:
        return jsonify({"error": str(e)})


# ---------------- HIT RATE ----------------
def calculate_hit_rate():
    hits = 0
    total = 0

    with open(LOG_FILE, "r") as f:
        lines = f.readlines()[-1000:]  # only recent activity

    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue

        status = parts[3]

        total += 1
        if "HIT" in status:
            hits += 1

    return round((hits / total) * 100, 2) if total else 0


@app.route("/squid/hit-rate")
def hit_rate():
    return jsonify({
        "hit_rate": calculate_hit_rate()
    })


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




@app.route("/squid/logs")
def squid_logs():
    data = parse_squid_logs()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)