from flask import Flask, render_template, jsonify, request
import subprocess, time, os, json
from squid_parser import parse_squid_logs, calculate_hit_rate

app = Flask(__name__)

# ---------------- PATHS ----------------
BASE_SQUID = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/squid_status"

START_SQUID   = f"{BASE_SQUID}/start_squid.sh"
STOP_SQUID    = f"{BASE_SQUID}/stop_squid.sh"
RESTART_SQUID = f"{BASE_SQUID}/restart_squid.sh"
RELOAD_SQUID  = f"{BASE_SQUID}/reload_squid.sh"

BLOCK_SCRIPT   = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/actions/block_site.sh"
UNBLOCK_SCRIPT = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/actions/unblock_site.sh"
CLEAR_SCRIPT   = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/actions/reset_lists.sh"

BLOCK_FILE    = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/blocked_sites.txt"
MANUAL_FILE   = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/manual_sites.txt"
CATEGORY_FILE = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/categories.json"

LOG_FILE = "/var/log/squid/access.log"
CONSOLE_LOGS = [] 

SCRIPT = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/cache/clear_cache.sh"


# ---------------- HELPERS ----------------
def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    out = result.stdout.strip()
    err = result.stderr.strip()
    if out:
        CONSOLE_LOGS.append(out)
    if err:
        CONSOLE_LOGS.append("ERROR: " + err)
    return out, err


def _log_error_response(exc, context=""):
    """Build a consistent JSON error body from an exception."""
    if isinstance(exc, PermissionError):
        msg = (
            f"Permission denied reading {LOG_FILE}. "
            "Fix with:  sudo chmod o+r /var/log/squid/access.log  "
            "and:  sudo chmod o+x /var/log/squid/"
        )
    elif isinstance(exc, FileNotFoundError):
        msg = f"{LOG_FILE} not found — is Squid running?"
    else:
        msg = str(exc)
    if context:
        msg = f"[{context}] {msg}"
    return msg


# ---------------- MANUAL SITES ----------------
def load_manual_sites():
    if not os.path.exists(MANUAL_FILE):
        try:
            with open(BLOCK_FILE) as f:
                sites = [x.strip() for x in f if x.strip()]
            save_manual_sites(sites)
            return sites
        except FileNotFoundError:
            return []
    try:
        with open(MANUAL_FILE) as f:
            return [x.strip() for x in f if x.strip()]
    except Exception:
        return []


def save_manual_sites(sites):
    os.makedirs(os.path.dirname(MANUAL_FILE), exist_ok=True)
    with open(MANUAL_FILE, "w") as f:
        for s in sorted(set(sites)):
            f.write(s + "\n")


# ---------------- CATEGORIES ----------------
def load_categories():
    if not os.path.exists(CATEGORY_FILE):
        return {}
    try:
        with open(CATEGORY_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_categories(data):
    os.makedirs(os.path.dirname(CATEGORY_FILE), exist_ok=True)
    with open(CATEGORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------- REBUILD BLOCKLIST ----------------
def rebuild_blocklist():
    manual    = set(load_manual_sites())
    cat_sites = set()
    for cat in load_categories().values():
        if cat.get("enabled"):
            cat_sites.update(cat.get("sites", []))

    merged = sorted(manual | cat_sites)

    os.makedirs(os.path.dirname(BLOCK_FILE), exist_ok=True)
    with open(BLOCK_FILE, "w") as f:
        for s in merged:
            f.write(s + "\n")

    subprocess.run(["sudo", "systemctl", "reload", "squid"])
    return merged


# ---------------- DASHBOARD ----------------
@app.route("/")
def home():
    return render_template("dashboard.html")


# ---------------- SQUID CONTROL ----------------
@app.route("/squid/start", methods=["POST"])
def start():
    out, err = run(["bash", START_SQUID])
    return jsonify({"output": out, "error": err})


@app.route("/squid/stop", methods=["POST"])
def stop():
    out, err = run(["bash", STOP_SQUID])
    return jsonify({"output": out, "error": err})


@app.route("/squid/restart", methods=["POST"])
def restart():
    out, err = run(["bash", RESTART_SQUID])
    return jsonify({"output": out, "error": err})


@app.route("/squid/reload", methods=["POST"])
def reload_config():
    out, err = run(["bash", RELOAD_SQUID])
    return jsonify({"output": out, "error": err})


# ---------------- LOG CLEAR ----------------
@app.route("/squid/clear-log", methods=["POST"])
def clear_log():
    try:
        subprocess.run(
            ["sudo", "truncate", "-s", "0", LOG_FILE], check=True
        )
        return jsonify({"output": "Log cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- MANUAL BLOCK / UNBLOCK ----------------
@app.route("/block", methods=["POST"])
def block():
    site = request.json.get("site", "").strip()
    if not site:
        return jsonify({"error": "No site provided"}), 400
    manual = load_manual_sites()
    if site not in manual:
        manual.append(site)
        save_manual_sites(manual)
    rebuild_blocklist()
    return jsonify({"output": f"Blocked {site}"})


@app.route("/unblock", methods=["POST"])
def unblock():
    site = request.json.get("site", "").strip()
    if not site:
        return jsonify({"error": "No site provided"}), 400
    manual = [s for s in load_manual_sites() if s != site]
    save_manual_sites(manual)
    rebuild_blocklist()
    return jsonify({"output": f"Unblocked {site}"})


@app.route("/clear", methods=["POST"])
def clear():
    save_manual_sites([])
    rebuild_blocklist()
    return jsonify({"output": "All manual blocks cleared"})


# ---------------- BLOCK LIST ----------------
@app.route("/lists")
def lists():
    try:
        with open(BLOCK_FILE) as f:
            blocked = [x.strip() for x in f if x.strip()]
    except Exception:
        blocked = []
    return jsonify({"blocked": blocked})


# ---------------- CATEGORY APIs ----------------
@app.route("/category/create", methods=["POST"])
def create_category():
    data  = request.json
    name  = data.get("name", "").strip()
    sites = [s.strip() for s in data.get("sites", []) if s.strip()]
    if not name:
        return jsonify({"error": "Category name is required"}), 400
    categories = load_categories()
    if name in categories:
        return jsonify({"error": "Category already exists"}), 409
    categories[name] = {"enabled": False, "sites": sites}
    save_categories(categories)
    return jsonify({"output": f"Category '{name}' created"})


@app.route("/category/toggle", methods=["POST"])
def toggle_category():
    name = request.json.get("name", "").strip()
    categories = load_categories()
    if name not in categories:
        return jsonify({"error": "Category not found"}), 404
    categories[name]["enabled"] = not categories[name].get("enabled", False)
    save_categories(categories)
    rebuild_blocklist()
    state = "enabled" if categories[name]["enabled"] else "disabled"
    return jsonify({"output": f"Category '{name}' {state}", "enabled": categories[name]["enabled"]})


@app.route("/category/delete", methods=["POST"])
def delete_category():
    name = request.json.get("name", "").strip()
    categories = load_categories()
    if name not in categories:
        return jsonify({"error": "Category not found"}), 404
    del categories[name]
    save_categories(categories)
    rebuild_blocklist()
    return jsonify({"output": f"Category '{name}' deleted"})


@app.route("/category/list")
def list_categories():
    return jsonify(load_categories())


# ---------------- LEGACY COMPAT ----------------
@app.route("/squid/sync-categories", methods=["POST"])
def sync_categories():
    rebuild_blocklist()
    return jsonify({"output": "Blocklist rebuilt and Squid reloaded"})


# ---------------- CONSOLE LOGS ----------------
@app.route("/logs")
def logs():
    return jsonify({"logs": CONSOLE_LOGS})


# ---------------- CACHE ----------------
@app.route("/squid/clear-cache", methods=["POST"])
def clear_cache():
    try:
        subprocess.run(["sudo", "systemctl", "stop",  "squid"],    check=True)
        subprocess.run(["sudo", "rm", "-rf", "/var/spool/squid/*"], check=True)
        subprocess.run(["sudo", "squid", "-z"],                     check=True)
        subprocess.run(["sudo", "systemctl", "start", "squid"],    check=True)
        return jsonify({"output": "Cache cleared successfully"})
    except Exception as e:
        return jsonify({"error": str(e)})


# ---------------- CRON LOG ----------------
@app.route("/squid/cron-log")
def cron_log():
    try:
        with open("/var/log/squid/cron.log") as f:
            lines = [l for l in f.readlines() if l.strip()]
        return jsonify({"last": lines[-1].strip() if lines else ""})
    except FileNotFoundError:
        return jsonify({"last": ""})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- HIT RATE ----------------
@app.route("/squid/hit-rate")
def hit_rate():
    try:
        return jsonify(calculate_hit_rate())
    except PermissionError as e:
        return jsonify({"error": _log_error_response(e, "hit-rate"), "hit_rate": 0, "cacheable_total": 0}), 200
    except FileNotFoundError as e:
        return jsonify({"error": _log_error_response(e, "hit-rate"), "hit_rate": 0, "cacheable_total": 0}), 200
    except Exception as e:
        return jsonify({"error": str(e), "hit_rate": 0, "cacheable_total": 0}), 200


# ---------------- STATUS ----------------
@app.route("/squid/status")
def squid_status():
    result = subprocess.run(
        ["systemctl", "is-active", "squid"], capture_output=True, text=True
    )
    status = result.stdout.strip()
    state  = "active" if status == "active" else ("inactive" if status == "inactive" else "unknown")
    return jsonify({"status": state})


# ---------------- PARSED ACCESS LOGS ----------------
@app.route("/squid/logs")
def squid_logs():
    try:
        return jsonify(parse_squid_logs())
    except PermissionError as e:
        return jsonify({"error": _log_error_response(e, "logs")}), 500
    except FileNotFoundError as e:
        return jsonify({"error": _log_error_response(e, "logs")}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)