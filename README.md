# SmartGate — Lab Proxy Management System

A full-featured Squid proxy management system for computer labs. Includes site blocking, time-based ACLs, detailed logging, a web dashboard, automated reports, and network enforcement via UFW + DHCP.

---

## Quick Start

```bash
git clone https://github.com/MRA810/SmartGate.git
cd SmartGate
sudo ./install.sh
```

The installer sets up Squid, UFW, cron jobs, and the Flask dashboard in one shot.

---

## Project Structure

```
SmartGate/
├── proxy/                  # Squid config and block lists
│   ├── squid.conf
│   ├── blocked_sites.txt
│   ├── allowed_sites.txt
│   └── categories/         # Category block lists (social, gaming, streaming)
├── scripts/
│   ├── proxy/              # start / stop / restart / reload
│   ├── acl/                # block_site / unblock_site / reset_lists
│   ├── cache/              # clear_cache
│   ├── network/            # setup_ufw / setup_dhcp
│   ├── reports/            # generate_report + report_generator.py
│   └── backup/             # backup_config / restore_config
├── dashboard/              # Flask admin dashboard
│   ├── app.py
│   ├── templates/
│   └── static/
├── logs/
│   └── reports/            # Generated daily/weekly reports
├── backups/                # Date-stamped config backups
├── docs/                   # Setup and usage guides
└── install.sh              # One-command installer
```

---

## Features

| # | Feature | Status |
|---|---------|--------|
| 1 | Squid proxy setup | ✅ Done |
| 2 | ACL site blocking | ✅ Done |
| 3 | Time-based blocking (8 AM–4 PM) | ✅ Done |
| 4 | Detailed logging | ✅ Done |
| 5 | Caching (4 GB, 512 MB memory) | ✅ Done |
| 6 | DHCP enforcement (dnsmasq + WPAD) | ✅ Done |
| 7 | Gateway lockdown (UFW + iptables) | ✅ Done |
| 8 | Web dashboard (Flask) | ✅ Done |
| 9 | Auto reports (PDF + Excel, cron) | ✅ Done |
| 10 | Backup & restore | ✅ Done |
| 11 | Category-based blocking | ✅ Done |
| 12 | Testing & monitoring | ✅ Done |

---

## Configuration

### 1. Set your subnet
Edit `proxy/squid.conf` — find `acl localnet src` and set your lab's subnet:
```
acl localnet src 192.168.1.0/24
```

### 2. Set proxy server IP
Edit `scripts/network/setup_dhcp.sh`:
```bash
PROXY_IP="192.168.1.1"
```

### 3. Dashboard credentials
Set environment variables before starting Flask:
```bash
export SMARTGATE_USER=admin
export SMARTGATE_PASS=your_secure_password
```

---

## Dashboard

Access at `http://SERVER_IP:5000`

- **Dashboard** — live traffic stats, charts, quick block/unblock
- **Logs** — searchable access log viewer
- **Rules** — manage block/allow lists and categories
- **Reports** — generate and download PDF/Excel reports

---

## Manual Script Usage

```bash
# Block / unblock a site
sudo ./scripts/acl/block_site.sh facebook.com
sudo ./scripts/acl/unblock_site.sh facebook.com

# Proxy control
sudo ./scripts/proxy/reload_squid.sh
sudo ./scripts/proxy/restart_squid.sh

# Generate a report now
sudo ./scripts/reports/generate_report.sh daily

# Backup config
sudo ./scripts/backup/backup_config.sh

# Restore config
sudo ./scripts/backup/restore_config.sh backups/smartgate_backup_2025-01-01_02-00-00.tar.gz
```

---

## Cron Jobs (installed automatically)

| Task | Schedule |
|------|----------|
| Daily report | Every day at 11:59 PM |
| Weekly report | Every Sunday at 11:58 PM |
| Config backup | Every day at 2 AM |
| Squid reload | Mon–Fri at 8 AM and 4 PM |

---

## Setting Up a Second Machine

```bash
git clone https://github.com/MRA810/SmartGate.git
cd SmartGate
sudo ./install.sh
```

Then update the subnet in `proxy/squid.conf` to match the new network.

---

## Tech Stack

- **OS** — Ubuntu 26 LTS
- **Proxy** — Squid
- **Firewall** — UFW / iptables
- **DHCP** — dnsmasq
- **Dashboard** — Flask + Chart.js
- **Reports** — ReportLab (PDF) + openpyxl (Excel)
- **Scheduler** — cron
