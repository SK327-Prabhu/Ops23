#!/usr/bin/env bash
# ==============================================================================
# Ops23 Service Management Helper
# Facilitates common systemd and application diagnostics on EC2 / AL2023
# ==============================================================================

SERVICE_NAME="ops23.service"

usage() {
    echo "Usage: $0 {status|start|stop|restart|logs|follow-logs|test-health|test-crash}"
    echo ""
    echo "Commands:"
    echo "  status       - Show systemctl status of ops23.service"
    echo "  start        - Start the ops23 systemd service"
    echo "  stop         - Stop the ops23 systemd service"
    echo "  restart      - Restart the ops23 systemd service"
    echo "  logs         - Display last 50 lines of journal logs"
    echo "  follow-logs  - Follow journal logs in real-time"
    echo "  test-health  - Query local http://127.0.0.1:8000/health"
    echo "  test-crash   - Trigger simulated crash to test systemd auto-restart"
    exit 1
}

case "${1:-}" in
    status)
        systemctl status "${SERVICE_NAME}"
        ;;
    start)
        sudo systemctl start "${SERVICE_NAME}"
        ;;
    stop)
        sudo systemctl stop "${SERVICE_NAME}"
        ;;
    restart)
        sudo systemctl restart "${SERVICE_NAME}"
        ;;
    logs)
        journalctl -u "${SERVICE_NAME}" -n 50 --no-pager
        ;;
    follow-logs)
        journalctl -u "${SERVICE_NAME}" -f
        ;;
    test-health)
        curl -i http://127.0.0.1:8000/health
        ;;
    test-crash)
        echo "Sending crash simulation request..."
        curl -i -X POST http://127.0.0.1:8000/api/simulate/crash \
             -H "Content-Type: application/json" \
             -d '{"delay_seconds": 0.5}'
        echo ""
        echo "Observing systemd restart in 6 seconds..."
        sleep 6
        systemctl status "${SERVICE_NAME}"
        ;;
    *)
        usage
        ;;
esac
