from datetime import datetime
from urllib.parse import urlparse

LOG_FILE = "/var/log/squid/access.log"


def extract_domain(url):
    # Extracting domain
    if not url or url == "-":
        return "UNKNOWN"

    # Grab the host
    if url.upper().startswith("CONNECT") or ("://" not in url and ":" in url and "/" not in url):
        try:
            host_port = url.split()[-1] if " " in url else url
            return host_port.split(":")[0]
        except Exception:
            return url

    if "://" not in url:
        url = "http://" + url

    try:
        parsed = urlparse(url)
        return parsed.netloc or url
    except Exception:
        return url


def parse_squid_logs(limit=300):
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()[-limit:]

    results = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) < 7:
            continue

        # --- timestamp ---
        try:
            timestamp = float(parts[0])
            dt = datetime.fromtimestamp(timestamp)
        except (ValueError, OSError):
            continue

        client_ip  = parts[2]
        cache_code = parts[3]          # e.g. TCP_MISS/200 or TCP_TUNNEL/200
        method     = parts[5]          # GET / CONNECT / POST …
        url        = parts[6]

        domain = extract_domain(url)

        results.append({
            "date":   dt.strftime("%Y-%m-%d"),
            "time":   dt.strftime("%H:%M:%S"),
            "ip":     client_ip,
            "site":   domain,
            "action": cache_code,
            "method": method,
        })

    # Return newest-first so the live log console shows recent traffic at top
    results.reverse()
    return results


def calculate_hit_rate(limit=1000):

    with open(LOG_FILE, "r") as f:
        lines = f.readlines()[-limit:]

    hit = miss = 0
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue
        code = parts[3]
        if "TUNNEL" in code:
            continue
        elif "HIT" in code:
            hit += 1
        else:
            miss += 1

    cacheable = hit + miss
    hit_rate  = round((hit / cacheable) * 100, 1) if cacheable else 0
    return {
        "hit_rate":       hit_rate,
        "cacheable_total": cacheable,
        "hits":           hit,
        "misses":         miss,
    }