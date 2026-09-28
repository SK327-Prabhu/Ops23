# EC2 Deployment and Systemd Service Guide

This guide details the procedure for deploying the **Ops23 FastAPI Application** to an AWS EC2 instance running **Amazon Linux 2023** using Python 3.12, a dedicated virtual environment, and `systemd`.

---

## 1. Prerequisites on EC2 (Amazon Linux 2023)

- **Target Host**: Amazon Linux 2023 (Instance ID: `i-0cd96b21b63e37feb`)
- **Python**: 3.12 runtime and development packages
- **Access**: AWS Systems Manager (SSM) Session Manager or Run Command
- **Target Location**: `/opt/ops23`
- **Application Port**: TCP 8000

---

## 2. Automated One-Step Installation

The repository includes an idempotent installation script at [`scripts/install_ec2.sh`](file:///d:/Ops23%20-%20Demo/ops23/scripts/install_ec2.sh).

### Via SSM Session Manager or Run Command:
```bash
# Clone or copy repository to instance
cd /tmp
# If cloned via git:
# git clone <repo_url> ops23 && cd ops23

# Make deployment script executable and run as root:
sudo chmod +x scripts/install_ec2.sh
sudo ./scripts/install_ec2.sh
```
### What the Script Performs Idempotently:
1. Installs Python 3.12 and pip via `dnf install -y python3.12 python3.12-pip` (relying on pre-installed `curl-minimal` in Amazon Linux 2023 to avoid package conflicts).
2. Creates the non-privileged system user `ops23` with no login shell (`/sbin/nologin`).
3. Creates the target directory `/opt/ops23` and log directory `/var/log/ops23`.
4. Copies `app/` and `requirements.txt` to `/opt/ops23`.
5. Builds a Python 3.12 virtual environment at `/opt/ops23/venv`.
6. Installs production dependencies from `requirements.txt`.
7. Sets ownership to `ops23:ops23`.
8. Copies `ops23.service` to `/etc/systemd/system/ops23.service`.
9. Reloads systemd daemon, enables, and restarts `ops23.service`.
10. Validates that `GET http://127.0.0.1:8000/health` returns HTTP 200.

---

## 3. Manual Step-by-Step Installation

If you prefer to configure the service manually:

### Step 1: Install Python 3.12
```bash
sudo dnf install -y python3.12 python3.12-pip
```

### Step 2: Create Service User and Application Directory
```bash
sudo useradd -r -s /sbin/nologin -d /opt/ops23 -c "Ops23 Service Account" ops23 || true
sudo mkdir -p /opt/ops23 /var/log/ops23
```

### Step 3: Copy Application Files
```bash
sudo cp -r app /opt/ops23/
sudo cp requirements.txt /opt/ops23/
```

### Step 4: Create Virtual Environment and Install Dependencies
```bash
sudo python3.12 -m venv /opt/ops23/venv
sudo /opt/ops23/venv/bin/pip install --upgrade pip
sudo /opt/ops23/venv/bin/pip install -r /opt/ops23/requirements.txt
sudo chown -R ops23:ops23 /opt/ops23 /var/log/ops23
sudo chmod 755 /opt/ops23
```

### Step 5: Install Systemd Service Unit
```bash
sudo cp infrastructure/systemd/ops23.service /etc/systemd/system/ops23.service
sudo chmod 644 /etc/systemd/system/ops23.service
sudo systemctl daemon-reload
sudo systemctl enable ops23.service
sudo systemctl start ops23.service
```

---

## 4. Systemd Service Configuration Details

The unit file is located at `/etc/systemd/system/ops23.service`:

```ini
[Unit]
Description=Ops23 FastAPI Application Service (AIOps Workload)
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ops23
Group=ops23
WorkingDirectory=/opt/ops23

# Environment and Path
Environment="PATH=/opt/ops23/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="ENVIRONMENT=production"
Environment="HOST=0.0.0.0"
Environment="PORT=8000"
Environment="SERVICE_NAME=Ops23"
Environment="APP_NAME=Ops23 API"
EnvironmentFile=-/opt/ops23/.env

# Application execution using virtual environment uvicorn
ExecStart=/opt/ops23/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info

# Automatic recovery and lifecycle
Restart=always
RestartSec=5s
KillSignal=SIGTERM
TimeoutStopSec=15s
FinalKillSignal=SIGKILL

# Logging configuration (journald with structured JSON preservation for Datadog)
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ops23

# Security hardening
PrivateTmp=true
ProtectSystem=full
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

---

## 5. Service Operations & Administration

### Check Service Status
```bash
systemctl status ops23.service
```

### Start / Stop / Restart Service
```bash
# Start service
sudo systemctl start ops23.service

# Stop service
sudo systemctl stop ops23.service

# Restart service
sudo systemctl restart ops23.service

# Reload systemd configuration after changes
sudo systemctl daemon-reload
```

### View Application Logs
Logs are emitted as structured JSON objects into `journald` tagged with `ops23`:

```bash
# View last 50 lines of logs
journalctl -u ops23.service -n 50 --no-pager

# Stream logs in real-time
journalctl -u ops23.service -f

# View logs from the past hour
journalctl -u ops23.service --since "1 hour ago"
```

---

## 6. Self-Healing & Failure Recovery Testing

The systemd service is configured with `Restart=always` and `RestartSec=5s`.

### Test Process Crash Simulation
You can trigger the controlled crash endpoint from EC2 or via SSM Run Command:

```bash
# Trigger controlled process termination
curl -X POST http://127.0.0.1:8000/api/simulate/crash \
     -H "Content-Type: application/json" \
     -d '{"delay_seconds": 0.5}'
```

Observe the systemd journal logs:
```bash
journalctl -u ops23.service -n 20 --no-pager
```
You will observe:
1. `CRITICAL` log indicating intentional crash simulation.
2. Systemd detecting process termination (`Main process exited, code=exited, status=1/FAILURE`).
3. Systemd waiting 5 seconds (`RestartSec=5s`).
4. Systemd automatically restarting `ops23.service`.
5. Health check returning `200 OK` on next check.
