# 🛡️ SmartGate

**SmartGate** is a full-featured, Linux-based network gateway management system built around [Squid Proxy](http://www.squid-cache.org/). It combines transparent web filtering, time-based access control, DHCP enforcement, firewall lockdown, a Flask web dashboard, and automated reporting — all deployable on a single Ubuntu gateway machine.

---

## ✅ Features

| # | Feature | Status |
|---|---------|--------|
| 1 | Squid proxy setup | ✅ Done |
| 2 | ACL site blocking | ✅ Done |
| 3 | Time-based blocking (8 AM–4 PM) | ✅ Done |
| 4 | Detailed logging | ✅ Done |
| 5 | Caching (4 GB disk, 512 MB memory) | ✅ Done |
| 6 | DHCP enforcement (dnsmasq + WPAD) | ✅ Done |
| 7 | Gateway lockdown (UFW + iptables) | ✅ Done |
| 8 | Web dashboard (Flask) | ✅ Done |
| 9 | Auto reports (PDF + Excel, cron) | ✅ Done |
| 10 | Backup & restore | ✅ Done |
| 11 | Category-based blocking | ✅ Done |
| 12 | Testing & monitoring | ✅ Done |

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| **OS** | Ubuntu 26 LTS |
| **Proxy** | Squid |
| **Firewall** | UFW / iptables |
| **DHCP** | dnsmasq |
| **Dashboard** | Flask + Chart.js |
| **Reports** | ReportLab (PDF) + openpyxl (Excel) |
| **Scheduler** | cron |

---

## 📁 Project Structure

```
SmartGate/
├── Squid Settings/        # Squid proxy configuration files (squid.conf, ACL lists)
├── block_site.sh          # Block a website via Squid ACL
├── unblock_site.sh        # Remove a website from the blocklist
├── clear_cache.sh         # Clear Squid's disk and memory cache
├── reload_squid.sh        # Reload Squid config without full restart
├── restart_squid.sh       # Fully restart the Squid service
├── start_squid.sh         # Start the Squid proxy service
└── reset_lists.sh         # Reset all block/allow lists to defaults
```

---

## ⚙️ Prerequisites

Ensure the following are installed on your Ubuntu 26 LTS gateway machine:

```bash
sudo apt update && sudo apt install -y \
  squid \
  dnsmasq \
  ufw \
  iptables \
  python3 python3-pip \
  cron
```

```bash
pip3 install flask reportlab openpyxl
```

**Required privileges:** All scripts and services require `sudo` / root access.

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/MRA810/SmartGate.git
cd SmartGate
```

### 2. Make Scripts Executable

```bash
chmod +x *.sh
```

### 3. Apply Squid Configuration

```bash
sudo cp "Squid Settings/"* /etc/squid/
sudo squid -k parse        # Validate config before applying
```

### 4. Start the Gateway

```bash
sudo ./start_squid.sh
```

---

## 📖 Script Reference

### `block_site.sh`
Adds a domain to the Squid ACL blocklist. Supports manual and category-based blocking.

```bash
sudo ./block_site.sh example.com
```

---

### `unblock_site.sh`
Removes a domain from the blocklist.

```bash
sudo ./unblock_site.sh example.com
```

---

### `start_squid.sh`
Starts the Squid proxy service if it is not already running.

```bash
sudo ./start_squid.sh
```

---

### `reload_squid.sh`
Reloads the Squid configuration without interrupting active connections. Run this after any ACL or config change.

```bash
sudo ./reload_squid.sh
```

---

### `restart_squid.sh`
Fully restarts the Squid service. Use after major configuration changes or cache operations.

```bash
sudo ./restart_squid.sh
```

---

### `clear_cache.sh`
Wipes Squid's cache (configured at 4 GB disk / 512 MB memory), freeing space and removing stale objects.

```bash
sudo ./clear_cache.sh
```

---

### `reset_lists.sh`
Resets all block and allow lists to their default state. Useful for a clean slate or after testing.

```bash
sudo ./reset_lists.sh
```

---

## 🔧 Feature Details

### 🔒 ACL & Category-Based Blocking
SmartGate uses Squid ACL lists to block individual domains or entire categories (e.g., social media, adult content, streaming). Domain lists are stored in flat files under `Squid Settings/` and can be updated without restarting the service.

### ⏰ Time-Based Blocking (8 AM – 4 PM)
Squid's `time` ACL enforces rules only during defined hours. Policies applied during working hours (08:00–16:00) are automatically lifted outside that window.

```squid
acl working_hours time MTWHF 08:00-16:00
http_access deny blocked_sites working_hours
```

### 📦 Caching
SmartGate caches web content to reduce bandwidth usage:
- **Disk cache:** 4 GB
- **Memory cache:** 512 MB

Cache behaviour is tuned in `Squid Settings/squid.conf`.

### 🌐 DHCP Enforcement (dnsmasq + WPAD)
`dnsmasq` acts as the network DHCP server and pushes a **WPAD (Web Proxy Auto-Discovery)** configuration to all clients, automatically directing their traffic through the SmartGate proxy — no manual browser configuration needed.

### 🔥 Gateway Lockdown (UFW + iptables)
Direct internet access is blocked at the OS level using UFW and iptables. All outbound HTTP/HTTPS traffic is redirected through Squid, ensuring no client can bypass the proxy.

```bash
# Example: redirect port 80 traffic through Squid
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 3128
```

### 📊 Web Dashboard (Flask + Chart.js)
A browser-based dashboard provides real-time visibility into:
- Top visited domains
- Blocked request counts
- Per-client traffic breakdown
- Live Squid service status

Run the dashboard:

```bash
python3 dashboard/app.py
```

Access at `http://<gateway-ip>:5000`

### 📄 Automated Reports (PDF + Excel)
SmartGate generates daily/weekly usage and blocking reports automatically via `cron`:
- **PDF** — formatted summaries using ReportLab
- **Excel** — raw tabular data using openpyxl

Example cron entry (daily report at midnight):

```cron
0 0 * * * /usr/bin/python3 /opt/smartgate/reports/generate_report.py
```

### 💾 Backup & Restore
Configuration and blocklists can be backed up and restored, making it easy to migrate SmartGate to a new machine or recover from misconfiguration.

### 📋 Detailed Logging
All HTTP requests are logged via Squid's native `access.log`. Logs include client IP, timestamp, URL, request status, and bytes transferred.

```bash
sudo tail -f /var/log/squid/access.log
```

### 🧪 Testing & Monitoring
Scripts and checks are included to verify:
- Proxy is intercepting traffic correctly
- Blocked sites are unreachable from client machines
- Squid service health and uptime

---

## 🔄 Typical Workflow

```
Start Gateway
    └── start_squid.sh

Block a site
    └── block_site.sh <domain>
    └── reload_squid.sh

Unblock a site
    └── unblock_site.sh <domain>
    └── reload_squid.sh

Clear cache
    └── clear_cache.sh → restart_squid.sh

Reset everything
    └── reset_lists.sh → restart_squid.sh

View reports
    └── Open Flask dashboard at http://<gateway-ip>:5000
    └── Check /reports/ folder for PDF/Excel files
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|---|---|
| Squid fails to start | Run `sudo squid -k parse` to check for config errors |
| Site still accessible after blocking | Run `./reload_squid.sh` or `./restart_squid.sh` |
| Cache not clearing | Stop Squid first, then run `./clear_cache.sh` |
| Clients not using proxy | Check dnsmasq WPAD config and iptables redirect rules |
| Dashboard not loading | Ensure Flask is running: `python3 dashboard/app.py` |
| Reports not generating | Check cron logs: `grep CRON /var/log/syslog` |
| Permission denied | Ensure scripts are run with `sudo` |

---

## 📄 License

This project is open-source. See the repository for details.

---

## 🤝 Contributing

Pull requests and suggestions are welcome. Please open an issue first to discuss any major changes.

---

> **SmartGate** — Enterprise-grade network access control, simplified.