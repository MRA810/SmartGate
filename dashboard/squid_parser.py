from datetime import datetime
from urllib.parse import urlparse

LOG_FILE = "/var/log/squid/access.log"


def extract_domain(url):
    if url == "-" or not url:
        return "UNKNOWN"

    # Handle CONNECT requests (HTTPS tunnels)
    if url.startswith("CONNECT"):
        try:
            return url.split()[1].split(":")[0]
        except:
            return "UNKNOWN"

    # Ensure parseable format
    if "://" not in url:
        url = "http://" + url

    try:
        return urlparse(url).netloc or "UNKNOWN"
    except:
        return "UNKNOWN"


def parse_squid_logs(limit=200):
    results = []

    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()[-limit:]
    except Exception:
        return []

    for line in lines:
        parts = line.split()
        if len(parts) < 7:
            continue

        # Timestamp safety check
        try:
            timestamp = float(parts[0])
            dt = datetime.fromtimestamp(timestamp)
        except:
            continue

        client_ip = parts[2]
        url = parts[6]

        domain = extract_domain(url)

        results.append({
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M:%S"),
            "ip": client_ip,
            "site": domain
        })

    return results