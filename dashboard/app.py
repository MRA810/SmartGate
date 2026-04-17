from flask import Flask, render_template, jsonify, request
import subprocess
import os
import json
from squid_parser import parse_squid_logs

app = Flask(__name__)

# ---------------- PATHS ----------------
BASE_SQUID = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/squid_status"

START_SQUID   = f"{BASE_SQUID}/start_squid.sh"
STOP_SQUID    = f"{BASE_SQUID}/stop_squid.sh"
RESTART_SQUID = f"{BASE_SQUID}/restart_squid.sh"
RELOAD_SQUID  = f"{BASE_SQUID}/reload_squid.sh"

BLOCK_SCRIPT  = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/actions/block_site.sh"
UNBLOCK_SCRIPT= "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/actions/unblock_site.sh"
CLEAR_SCRIPT  = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/actions/reset_lists.sh"

# blocked_sites.txt  →  manual entries live here AND category entries are merged in
BLOCK_FILE    = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/blocked_sites.txt"
# manual_sites.txt   →  source-of-truth for sites the user added manually (never touched by categories)
MANUAL_FILE   = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/manual_sites.txt"
CATEGORY_FILE = "/home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/proxy/categories.json"

LOG_FILE = "/var/log/squid/access.log"
LOGS = []

# ---------------- HELPERS ----------------
def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    out = result.stdout.strip()
    err = result.stderr.strip()
    if out:
        LOGS.append(out)
    if err:
        LOGS.append("ERROR: " + err)
    return out, err


# ---------------- MANUAL SITES (source-of-truth) ----------------
def load_manual_sites():
    """Return the list of manually-blocked sites (from manual_sites.txt)."""
    if not os.path.exists(MANUAL_FILE):
        # First run: seed from existing blocked_sites.txt so nothing is lost
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


# ---------------- CATEGORY SYSTEM ----------------
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


# ---------------- CORE: rebuild_blocklist ----------------
def rebuild_blocklist():
    """
    Merge manual_sites.txt  +  all *enabled* category sites
    → write the result to blocked_sites.txt
    → reload squid
    This is the single source of truth writer.
    """
    manual   = set(load_manual_sites())
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
def reload():
    out, err = run(["bash", RELOAD_SQUID])
    return jsonify({"output": out, "error": err})


# ---------------- LOG CLEAR ----------------
@app.route("/squid/clear-log", methods=["POST"])
def clear_log():
    try:
        subprocess.run(["sudo", "truncate", "-s", "0", "/var/log/squid/access.log"], check=True)
        return jsonify({"output": "Log cleared"})
    except Exception as e:
        return jsonify({"error": str(e)})


# ---------------- MANUAL BLOCK / UNBLOCK ----------------
@app.route("/block", methods=["POST"])
def block():
    site = request.json.get("site", "").strip()
    if not site:
        return jsonify({"error": "No site provided"})
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
        return jsonify({"error": "No site provided"})
    manual = load_manual_sites()
    manual = [s for s in manual if s != site]
    save_manual_sites(manual)
    rebuild_blocklist()
    return jsonify({"output": f"Unblocked {site}"})


@app.route("/clear", methods=["POST"])
def clear():
    """Clear ALL manual blocks (category blocks are untouched)."""
    save_manual_sites([])
    rebuild_blocklist()
    return jsonify({"output": "All manual blocks cleared"})


# ---------------- BLOCK LIST (what squid is actually enforcing) ----------------
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
    data = request.json
    name  = data.get("name", "").strip()
    sites = [s.strip() for s in data.get("sites", []) if s.strip()]

    if not name:
        return jsonify({"error": "Category name is required"})

    categories = load_categories()
    if name in categories:
        return jsonify({"error": "Category already exists"})

    categories[name] = {"enabled": False, "sites": sites}
    save_categories(categories)
    return jsonify({"output": f"Category '{name}' created"})


@app.route("/category/toggle", methods=["POST"])
def toggle_category():
    data = request.json
    name = data.get("name", "").strip()

    categories = load_categories()
    if name not in categories:
        return jsonify({"error": "Category not found"})

    # Flip the enabled state
    categories[name]["enabled"] = not categories[name].get("enabled", False)
    save_categories(categories)
    rebuild_blocklist()

    state = "enabled" if categories[name]["enabled"] else "disabled"
    return jsonify({"output": f"Category '{name}' {state}", "enabled": categories[name]["enabled"]})


@app.route("/category/delete", methods=["POST"])
def delete_category():
    data = request.json
    name = data.get("name", "").strip()

    categories = load_categories()
    if name not in categories:
        return jsonify({"error": "Category not found"})

    del categories[name]
    save_categories(categories)
    rebuild_blocklist()
    return jsonify({"output": f"Category '{name}' deleted"})


@app.route("/category/list")
def list_categories():
    return jsonify(load_categories())


# ---------------- LEGACY SYNC ENDPOINT (kept for compatibility) ----------------
@app.route("/squid/sync-categories", methods=["POST"])
def sync_categories():
    rebuild_blocklist()
    return jsonify({"output": "Blocklist rebuilt and Squid reloaded"})


# ---------------- CONSOLE LOGS ----------------
@app.route("/logs")
def logs():
    return jsonify({"logs": LOGS})


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
            lines = f.readlines()
        return jsonify({"last": lines[-1] if lines else ""})
    except Exception as e:
        return jsonify({"error": str(e)})


# ---------------- HIT RATE ----------------
def calculate_hit_rate():
    hits = total = 0
    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()[-1000:]
    except Exception:
        return 0
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue
        total += 1
        if "HIT" in parts[3]:
            hits += 1
    return round((hits / total) * 100, 2) if total else 0


@app.route("/squid/hit-rate")
def hit_rate():
    return jsonify({"hit_rate": calculate_hit_rate()})


# ---------------- STATUS ----------------
@app.route("/squid/status")
def squid_status():
    result = subprocess.run(["systemctl", "is-active", "squid"], capture_output=True, text=True)
    status = result.stdout.strip()
    state  = "active" if status == "active" else ("inactive" if status == "inactive" else "unknown")
    return jsonify({"status": state})


# ---------------- PARSED LOGS ----------------
@app.route("/squid/logs")
def squid_logs():
    data = parse_squid_logs()
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)