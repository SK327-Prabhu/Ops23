#!/usr/bin/env bash
# ==============================================================================
# Ops23 - EC2 Automated Deployment & Systemd Bootstrap Script
# Target OS: Amazon Linux 2023
# Python: 3.12
# Deployment Target: /opt/ops23
# Service: ops23.service
# ==============================================================================

set -euo pipefail

APP_DIR="/opt/ops23"
LOG_DIR="/var/log/ops23"
SERVICE_NAME="ops23.service"
APP_USER="ops23"
APP_GROUP="ops23"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== [Ops23] Starting EC2 Deployment Bootstrap ==="

# 1. Require root or sudo privileges
if [[ $EUID -ne 0 ]]; then
   echo "[ERROR] This script must be run as root or with sudo." >&2
   exit 1
fi

# 2. Install Python 3.12 and dependencies on Amazon Linux 2023
# Note: Amazon Linux 2023 includes curl-minimal by default. Installing the full 'curl'
# package causes a package manager conflict, so we only install Python 3.12 and pip.
echo "--> Installing Python 3.12 and runtime dependencies via dnf..."
dnf check-update || true
dnf install -y python3.12 python3.12-pip

# 3. Create dedicated system user and group (least-privilege)
if ! id -u "${APP_USER}" &>/dev/null; then
    echo "--> Creating dedicated system user: ${APP_USER}"
    useradd -r -s /sbin/nologin -d "${APP_DIR}" -c "Ops23 Service Account" "${APP_USER}"
else
    echo "--> System user ${APP_USER} already exists."
fi

# 4. Prepare directories
echo "--> Setting up application and log directories..."
mkdir -p "${APP_DIR}"
mkdir -p "${LOG_DIR}"

# 5. Sync application files to /opt/ops23
echo "--> Copying application files to ${APP_DIR}..."
cp -r "${REPO_ROOT}/app" "${APP_DIR}/"
cp "${REPO_ROOT}/requirements.txt" "${APP_DIR}/"

# 6. Setup Python 3.12 Virtual Environment
echo "--> Creating Python 3.12 virtual environment at ${APP_DIR}/venv..."
if [[ ! -d "${APP_DIR}/venv" ]]; then
    python3.12 -m venv "${APP_DIR}/venv"
fi

echo "--> Upgrading pip and installing requirements..."
"${APP_DIR}/venv/bin/pip" install --upgrade pip --quiet
"${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/requirements.txt" --quiet

# 7. Apply proper ownership and permissions
echo "--> Setting file permissions..."
chown -R "${APP_USER}:${APP_GROUP}" "${APP_DIR}"
chown -R "${APP_USER}:${APP_GROUP}" "${LOG_DIR}"
chmod 755 "${APP_DIR}"

# 8. Install and configure systemd service
echo "--> Installing systemd unit file..."
SERVICE_SOURCE="${REPO_ROOT}/infrastructure/systemd/${SERVICE_NAME}"
if [[ ! -f "${SERVICE_SOURCE}" && -f "${SCRIPT_DIR}/${SERVICE_NAME}" ]]; then
    SERVICE_SOURCE="${SCRIPT_DIR}/${SERVICE_NAME}"
fi

if [[ ! -f "${SERVICE_SOURCE}" ]]; then
    echo "[ERROR] Service unit file not found at ${SERVICE_SOURCE}" >&2
    exit 1
fi

cp "${SERVICE_SOURCE}" "/etc/systemd/system/${SERVICE_NAME}"
chmod 644 "/etc/systemd/system/${SERVICE_NAME}"

echo "--> Reloading systemd daemon and enabling ${SERVICE_NAME}..."
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"

echo "--> Starting ${SERVICE_NAME}..."
systemctl restart "${SERVICE_NAME}"

# 9. Verify deployment
echo "--> Verifying service health..."
sleep 2

if systemctl is-active --quiet "${SERVICE_NAME}"; then
    echo "[SUCCESS] ${SERVICE_NAME} is active and running!"
else
    echo "[ERROR] ${SERVICE_NAME} failed to start. Showing recent journal logs:" >&2
    journalctl -u "${SERVICE_NAME}" -n 20 --no-pager >&2
    exit 1
fi

# 10. Smoke test /health endpoint locally
echo "--> Performing local /health HTTP check..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health || true)

if [[ "${HEALTH_CHECK}" == "200" ]]; then
    echo "[SUCCESS] Health check passed (HTTP 200)!"
    curl -s http://127.0.0.1:8000/health | python3.12 -m json.tool || true
else
    echo "[WARNING] Health check returned HTTP ${HEALTH_CHECK}. Check logs with: journalctl -u ${SERVICE_NAME} -f"
fi

echo "=== [Ops23] Deployment Complete ==="
