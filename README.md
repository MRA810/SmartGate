# 🛡️ SmartGate

**SmartGate** is a web-based admin dashboard for managing and controlling a **Squid proxy server** through a clean UI — no terminal required. Admins can block/unblock sites, manage access lists, control the Squid service, and clear the cache, all from a browser interface. The dashboard is powered by a **Flask** backend that executes shell scripts on the server, and a **crontab** job handles automatic cache clearing every 24 hours.

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [Shell Scripts](#shell-scripts)
- [Crontab Integration](#crontab-integration)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Squid Configuration](#squid-configuration)
- [Requirements](#requirements)
- [Contributing](#contributing)

---

## ✨ Features

- **Block Sites** — Add domains to Squid's blocklist instantly via the UI
- **Unblock Sites** — Remove domains from the blocklist with a single click
- **Start / Stop / Restart / Reload Squid** — Control the Squid service lifecycle from the dashboard
- **Clear Cache** — Flush Squid's disk cache on demand
- **Reset Lists** — Restore allow/block lists to their default state
- **Live Squid Log Parsing** — `squid_parser.py` reads and surfaces Squid access logs in the dashboard
- **Automated Cache Clearing** — A crontab job automatically clears the cache every 24 hours

---

## 🧰 Tech Stack

| Layer        | Technology                 |
| ------------ | -------------------------- |
| Frontend     | HTML, CSS                  |
| Backend      | Python, Flask              |
| Log Parsing  | Python (`squid_parser.py`) |
| Proxy Engine | Squid Proxy Server         |
| Automation   | Bash Shell Scripts         |
| Scheduling   | Crontab                    |

---

## 📁 Project Structure

```
SmartGate/
├── dashboard/                        # Flask web application
│   ├── app.py                        # Flask app — routes, subprocess calls, dashboard logic
│   ├── squid_parser.py               # Parses Squid access logs for the dashboard UI
│   ├── requirements.txt              # Python dependencies
│   ├── run.sh                        # Convenience script to launch the Flask app
│   └── templates/
│       ├── dashboard.html            # Main dashboard UI template
│       └── CSS_color.txt             # Color reference / CSS design notes
│
├── proxy/                            # Squid proxy configuration & access lists
│   ├── squid.conf.backup             # Backup of the Squid configuration file
│   ├── blocked_sites.txt             # Domains currently allowed
│   ├── manual_sites.txt              # Manually managed domain entries
│   └── categories.json              # Site category definitions for grouping rules
│
├── Scripts/                          # Shell scripts executed by Flask via subprocess
│   ├── actions/
│   │   ├── block_site.sh             # Appends a domain to blocked_sites.txt & reloads Squid
│   │   ├── unblock_site.sh           # Removes a domain from blocked_sites.txt & reloads Squid
│   │   └── reset_lists.sh            # Resets blocked/whitelist files to defaults
│   ├── cache/
│   │   └── clear_cache.sh            # Stops Squid, wipes cache directory, restarts Squid
│   └── squid_status/
│       ├── start_squid.sh            # Starts the Squid service
│       ├── stop_squid.sh             # Stops the Squid service
│       ├── restart_squid.sh          # Fully restarts Squid
│       └── reload_squid.sh           # Reloads Squid config without dropping connections
│
└── README.md
```

---

## 🏗️ Architecture Overview

SmartGate ties together three layers — the Flask dashboard, the shell scripts, and the Squid proxy — in a straightforward pipeline:

```
[ Admin Browser ]
       │
       │  HTTP request (e.g. "Block site: example.com")
       ▼
[ Flask — app.py ]
       │
       │  subprocess.run(["bash", "Scripts/actions/block_site.sh", "example.com"])
       ▼
[ Shell Script ]
       │
       │  Writes to proxy/blocked_sites.txt
       │  Signals Squid: squid -k reconfigure
       ▼
[ Squid Proxy Server ]
       │
       │  Enforces updated ACL rules for all network traffic
       ▼
[ Network / Clients ]
```

### How Flask Calls the Shell Scripts

Every admin action in the dashboard maps to a Flask route in `app.py`. When an action is triggered, Flask uses Python's `subprocess.run()` to execute the corresponding shell script on the server with the required arguments:

```python
# Example: blocking a site
import subprocess
from flask import request, redirect

@app.route('/block', methods=['POST'])
def block_site():
    domain = request.form['domain']
    subprocess.run(['bash', 'Scripts/actions/block_site.sh', domain], check=True)
    return redirect('/')
```

The shell script modifies the relevant file in `proxy/` (e.g. `blocked_sites.txt`) and signals Squid to reload its configuration, making the change live immediately — no full Squid restart needed for most operations.

### How Squid Reads the Lists

Squid is configured via `squid.conf` to read its ACL rules from the flat text files in `proxy/`:

```squid
acl blocked_sites dstdomain "/etc/squid/blocked_sites.txt"

http_access deny  blocked_sites
```

When a shell script updates one of these files and calls `squid -k reconfigure`, Squid picks up the new entries without a full restart.

### Log Parsing

`squid_parser.py` reads Squid's access log (typically at `/var/log/squid/access.log`), parses the raw log format into structured data, and passes it to the Flask template so admins can view live proxy traffic directly on the dashboard — without touching the terminal.

---

## 🐚 Shell Scripts

| Script             | Location                | Description                                                 |
| ------------------ | ----------------------- | ----------------------------------------------------------- |
| `block_site.sh`    | `Scripts/actions/`      | Adds a domain to `blocked_sites.txt` and reloads Squid      |
| `unblock_site.sh`  | `Scripts/actions/`      | Removes a domain from `blocked_sites.txt` and reloads Squid |
| `reset_lists.sh`   | `Scripts/actions/`      | Resets `blocked_sites.txt` and `whitelist.txt` to defaults  |
| `clear_cache.sh`   | `Scripts/cache/`        | Stops Squid, wipes the cache directory, restarts Squid      |
| `start_squid.sh`   | `Scripts/squid_status/` | Starts the Squid service                                    |
| `stop_squid.sh`    | `Scripts/squid_status/` | Stops the Squid service                                     |
| `restart_squid.sh` | `Scripts/squid_status/` | Fully restarts Squid                                        |
| `reload_squid.sh`  | `Scripts/squid_status/` | Reloads Squid config without dropping active connections    |

---

## ⏰ Crontab Integration

SmartGate uses a crontab job to automatically clear the Squid cache every 24 hours, preventing the cache from growing unbounded without manual admin intervention.

### How It Works

```
[ Crontab — runs at midnight daily ]
       │
       │  Executes: Scripts/cache/clear_cache.sh
       ▼
[ clear_cache.sh ]
       │
       ├── systemctl stop squid
       ├── rm -rf /var/spool/squid/*   (wipes cache directory)
       ├── squid -z                    (reinitialises cache structure)
       └── systemctl start squid
```

### Setting Up the Cron Job

Add the following entry to your crontab with `crontab -e`:

```cron
00 20 * * * /home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/cache/clear_cache.sh
```

This runs `clear_cache.sh` at **midnight every day**. Output is logged to `/var/log/smartgate_cache.log` for auditing.

### Verify the Cron Job Is Active

```bash
crontab -l
```

---

## 🚀 Getting Started

### Prerequisites

- Linux server (Ubuntu/Debian recommended)
- Squid proxy installed:
  ```bash
  sudo apt update && sudo apt install squid -y
  ```
- Python 3.10+:
  ```bash
  sudo apt install python3 python3-pip -y
  ```

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/MRA810/SmartGate.git
   cd SmartGate
   ```

2. **Install Python dependencies**

   ```bash
   cd dashboard
   pip install -r requirements.txt
   ```

3. **Make all shell scripts executable**

   ```bash
   chmod +x Scripts/actions/*.sh
   chmod +x Scripts/cache/*.sh
   chmod +x Scripts/squid_status/*.sh
   chmod +x dashboard/run.sh
   ```

4. **Copy proxy list files to Squid's config directory**

   ```bash
   sudo cp proxy/blocked_sites.txt /etc/squid/
   sudo cp proxy/whitelist.txt /etc/squid/
   sudo cp proxy/manual_sites.txt /etc/squid/
   ```

5. **Apply your Squid configuration**

   ```bash
   sudo cp proxy/squid.conf.backup /etc/squid/squid.conf
   sudo systemctl restart squid
   ```

6. **Set up the crontab for automatic cache clearing**

   ```bash
   crontab -e
   # Add the following line:
   # 00 20 * * * /home/ashraful/Desktop/Coding_Nerdy_Stuffs/SmartGate/Scripts/cache/clear_cache.sh
   ```

7. **Start the Flask dashboard**
   ```bash
   cd dashboard
   bash run.sh
   # or: python3 app.py
   ```

The dashboard will be available at `http://localhost:5000` by default.

---

## 🖥️ Usage

Once the dashboard is running in your browser:

- Use the **Block / Unblock** panel to manage domain access in real time
- Use the **Service Controls** section to start, stop, restart, or reload Squid
- Click **Clear Cache** to immediately purge cached content
- Click **Reset Lists** to revert block/whitelist files to their defaults
- View **live Squid traffic** parsed from the access log directly on the dashboard

---

## ⚙️ Squid Configuration

The `proxy/` directory holds all ACL list files that Squid reads at runtime:

| File                | Purpose                                     |
| ------------------- | ------------------------------------------- |
| `blocked_sites.txt` | Domains denied by Squid's ACL rules         |
| `whitelist.txt`     | Domains explicitly allowed through          |
| `manual_sites.txt`  | Manually curated domain entries             |
| `categories.json`   | Category groupings for organising rules     |
| `squid.conf.backup` | Reference backup of the Squid configuration |

Squid must be configured to reference these files in `/etc/squid/squid.conf` using `acl` directives (see [Architecture Overview](#architecture-overview)).

---

## 📦 Requirements

| Requirement | Version                    |
| ----------- | -------------------------- |
| Python      | 3.10+                      |
| Flask       | See `requirements.txt`     |
| Squid       | 4.x or higher              |
| Bash        | 4.x or higher              |
| OS          | Ubuntu 20.04+ / Debian 10+ |

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

Please make sure any new shell scripts are well-commented and tested before submitting.

---

> **SmartGate** — Putting proxy control in the hands of admins, not the terminal.
