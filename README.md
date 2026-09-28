# Ops23: AI-Powered Cloud Operations & Automated Incident Response

## Application Overview: Ops23 API

**Ops23 API** is a production-oriented, cloud-native FastAPI application built to serve as the monitored workload in the Ops23 AIOps architecture.

The application runs on AWS EC2, delivers core business APIs, produces structured JSON telemetry for Datadog log monitoring, and provides controlled failure simulation hooks for testing automated incident recovery loops driven by AWS Systems Manager (SSM).

---

## Architecture & Operational Lifecycle

```
┌──────────────────┐       JSON Telemetry       ┌──────────────────┐
│    Ops23 API     │ ─────────────────────────> │  Datadog Agent   │
│  (AWS EC2 Host)  │     (Logs, Traces, /health)│ (Monitors & Alarms)
└──────────────────┘                            └────────┬─────────┘
         ▲                                               │ Alert / Webhook
         │                                               ▼
┌──────────────────┐        SSM Automation      ┌──────────────────┐
│     AWS SSM      │ <───────────────────────── │  Ops23 Incident  │
│  (Auto-Recovery) │       (Restart/Remediate)  │ Triage & Agent   │
└──────────────────┘                            └──────────────────┘
```

### Incident Lifecycle
1. **Telemetry Ingestion**: Every HTTP request and lifecycle event is logged as structured JSON with UTC timestamps, log level, request correlation IDs (`X-Request-ID`), endpoint paths, and execution durations.
2. **Anomaly Detection**: Datadog monitors track error rates (e.g. 5xx spikes or unhandled exceptions from `/api/simulate/error`) and service downtime (unhealthy `/health` or dead process from `/api/simulate/crash`).
3. **Automated Remediation**: AWS SSM executes targeted remediation runbooks (e.g., systemd service restart, log rotation, cache reset).
4. **Verification**: Post-remediation verification queries `/health` to validate that the service is operational.

---

## Available Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API welcome metadata, service status, and link directory. |
| `GET` | `/health` | Lightweight service health check reporting uptime status and timestamp. |
| `GET` | `/api/users` | Lists registered users (DevOps, Cloud Architects, SREs). |
| `GET` | `/api/orders` | Lists business transactions and order processing statuses. |
| `POST` | `/api/simulate/error` | **Controlled failure simulation**: Intentionally triggers an application exception, emits a structured ERROR log with full stack trace, and returns HTTP 500. |
| `POST` | `/api/simulate/crash` | **Controlled crash simulation**: Emits a CRITICAL log and initiates an application process exit (`os._exit(1)`) to test auto-recovery mechanisms. |
| `GET` | `/docs` | Interactive Swagger / OpenAPI documentation UI. |
| `GET` | `/redoc` | Alternative ReDoc documentation UI. |

---

## Failure Simulation Endpoints Explained

The simulation endpoints enable deterministic testing of observability and self-healing automation without needing manual server sabotage:

### 1. `POST /api/simulate/error`
- **Purpose**: Generates an application-level error to test Datadog log parsing, error rate monitors, and AI anomaly triage.
- **Behavior**:
  - Accepts an optional JSON body: `{"message": "Custom error reason", "error_code": "CUSTOM_ERR"}`.
  - Logs a structured `ERROR` log containing error code, request ID, endpoint, and stack trace.
  - Caught by the centralized exception handler to return a consistent HTTP 500 JSON response:
    ```json
    {
      "error": "InternalServerError",
      "message": "An application error occurred. Incident logged for operational analysis.",
      "detail": "Simulated application failure: unexpected internal processing error",
      "request_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "timestamp": "2026-09-28T07:05:00.000000+00:00"
    }
    ```

### 2. `POST /api/simulate/crash`
- **Purpose**: Simulates an unrecoverable process crash to test host-level service supervisors (e.g., systemd) and AWS SSM automated restart runbooks.
- **Behavior**:
  - Accepts an optional JSON body: `{"delay_seconds": 0.5}`.
  - Emits a structured `CRITICAL` log indicating that the process is shutting down.
  - Returns an immediate HTTP 200 acknowledgment with `{"status": "crash_initiated"}` before exiting.
  - Terminates the Python process using `os._exit(1)` after the configured delay. *(Note: Automatically bypassed during automated unit tests to protect the test runner).*

---

## Structured Logging & Redaction

Ops23 API implements lightweight structured JSON logging using Python's standard `logging` library.

### Key Features:
- **Datadog-Ready JSON**: Each log line is a standalone JSON object containing `timestamp`, `level`, `service`, `endpoint`, `request_id`, `message`, and `error` details.
- **Context Correlation**: Uses `contextvars` to propagate `X-Request-ID` and `endpoint` across async calls.
- **Security & Privacy**: Automatically redacts sensitive fields (such as `password`, `token`, `secret`, `authorization`, `api_key`) to prevent data leakage in logs.

**Sample Log Record:**
```json
{
  "timestamp": "2026-09-28T07:05:12.345678+00:00",
  "level": "INFO",
  "service": "Ops23",
  "logger": "ops23",
  "message": "Completed request: GET /api/users -> 200 (1.42ms)",
  "request_id": "4a761e2f-5ec4-41d3-864b-852dc8d6c701",
  "endpoint": "/api/users",
  "http_method": "GET",
  "http_status_code": 200,
  "duration_ms": 1.42
}
```

---

## Getting Started & Running Locally

### 1. Prerequisites
- Python 3.10+
- Virtual environment (`venv`)

### 2. Setup

```bash
# Navigate to ops23 project
cd "d:\Ops23 - Demo\ops23"

# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Activate on Linux/macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application

```bash
# Start server with Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

*Or run via the module entrypoint:*
```bash
python -m app.main
```

### 4. Test Sample Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Users
curl http://localhost:8000/api/users

# Orders
curl http://localhost:8000/api/orders

# Simulate Application Error (Generates structured ERROR log and returns 500)
curl -X POST http://localhost:8000/api/simulate/error -H "Content-Type: application/json" -d '{"message": "Database pool exhausted"}'

# Simulate Process Crash (Generates CRITICAL log and terminates process)
curl -X POST http://localhost:8000/api/simulate/crash -H "Content-Type: application/json" -d '{"delay_seconds": 1.0}'
```

---

## Running the Automated Test Suite

Run the full suite of unit and integration tests using `pytest`:

```bash
pytest -v
```

All 9 tests validate endpoint routing, response schemas, error handling, request ID propagation, and JSON logging redaction.

---

## Phase 2: Cloud Infrastructure (Terraform)

The infrastructure code is defined under [`infrastructure/terraform/`](file:///d:/Ops23%20-%20Demo/ops23/infrastructure/terraform).

> [!IMPORTANT]
> **Status**: Prepared & Validated. Resources have **NOT** been applied or deployed to AWS.

### 1. What the Infrastructure Creates
- **EC2 Instance** (`aws_instance.app_server`): Dedicated host configured to run the Ops23 FastAPI application on Amazon Linux 2023 with encrypted gp3 storage.
- **Security Group** (`aws_security_group.app_sg`): Controls traffic to the instance. Allows inbound TCP port `8000` for application traffic and health checks, and allows outbound internet access for telemetry and package updates.
- **IAM Role & Instance Profile** (`aws_iam_role.ec2_role`, `aws_iam_instance_profile.ec2_profile`): Grants the EC2 instance identity and permissions in AWS.
- **AWS SSM Managed Policy Attachment** (`aws_iam_role_policy_attachment.ssm_managed_instance_core`): Attaches the AWS-managed policy `AmazonSSMManagedInstanceCore` to the EC2 role, enabling AWS Systems Manager to manage the instance.

### 2. Why AWS Systems Manager (SSM) is Used
- **Automated Incident Remediation**: SSM Run Command and Automation Documents allow the AIOps remediation pipeline to execute automated runbooks (e.g., service restart, clearing stale locks, diagnostic dumping) programmatically without human intervention.
- **Zero-Trust Fleet Management**: SSM maintains centralized audit logs in CloudTrail of every command executed on the host.
- **Reliable Heartbeats**: The SSM Agent reports instance status and inventory continuously to AWS.

### 3. Why SSH is NOT Required
- **No Inbound Port 22**: Opening SSH port 22 creates an unnecessary attack vector and requires managing, rotating, and distributing static `.pem` key pairs.
- **SSM Session Manager**: Operators and automated agents connect securely via IAM credentials and TLS using AWS Session Manager (`aws ssm start-session --target <instance-id>`). All access is authenticated through AWS IAM and logged with full session auditing.

### 4. How Terraform Will Eventually Be Initialized and Applied

When ready to deploy in later phases:

```bash
# 1. Navigate to the terraform directory
cd infrastructure/terraform

# 2. Configure variables (copy example file)
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars to configure region or instance sizing if desired

# 3. Authenticate with AWS (uses standard credential chain: AWS CLI or environment variables)
aws sts get-caller-identity

# 4. Initialize Terraform (downloads provider plugins)
terraform init

# 5. Preview changes before applying
terraform plan

# 6. Apply infrastructure (when explicitly instructed)
terraform apply
```

---

## Phase 3: EC2 Deployment & Systemd Service

For Amazon Linux 2023 (`i-0cd96b21b63e37feb`), the application runs under `systemd` as a managed background service using Python 3.12 and a dedicated virtual environment.

### 1. Automated Installation
Run the automated installation script via AWS SSM Session Manager or Run Command:

```bash
sudo chmod +x scripts/install_ec2.sh
sudo ./scripts/install_ec2.sh
```

### 2. Systemd Service Unit (`ops23.service`)
The unit file is installed to `/etc/systemd/system/ops23.service`:
- **Working Directory**: `/opt/ops23`
- **User / Group**: Dedicated unprivileged `ops23:ops23`
- **Virtualenv**: `/opt/ops23/venv/bin/uvicorn`
- **Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`
- **Restart Policy**: `Restart=always` with `RestartSec=5s` (automatic recovery on failure)
- **Logging**: Preserved structured JSON logs sent directly to `journald` with `SyslogIdentifier=ops23`

### 3. Service Administration Commands

```bash
# Check service status
systemctl status ops23.service

# Start the service
sudo systemctl start ops23.service

# Stop the service
sudo systemctl stop ops23.service

# Restart the service
sudo systemctl restart ops23.service

# Reload systemd configuration after changes
sudo systemctl daemon-reload

# View recent service logs (JSON formatted)
journalctl -u ops23.service -n 50 --no-pager

# Tail logs in real-time
journalctl -u ops23.service -f
```

For full details and troubleshooting, see the [EC2 Deployment Guide](file:///d:/Ops23%20-%20Demo/ops23/docs/ec2_deployment.md).
