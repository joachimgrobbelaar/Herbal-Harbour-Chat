#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

MODE="${1:-all}"

start_backend() {
    echo "🌿 [Herbal Harbour] Starting FastAPI Core Engine..."
    "$PROJECT_ROOT/.venv/bin/uvicorn" src.main:app --host 0.0.0.0 --port 8000 --reload
}

start_wa_bridge() {
    echo "📱 [Herbal Harbour] Starting WhatsApp Baileys QR Bridge..."
    cd "$PROJECT_ROOT/bridges/whatsapp"
    node bridge.js
}

case "$MODE" in
    backend)
        start_backend
        ;;
    wa-bridge)
        start_wa_bridge
        ;;
    all)
        echo "🚀 Starting Herbal Harbour Services (FastAPI on :8000 & WhatsApp Bridge on :3001)..."
        trap 'kill $(jobs -p) 2>/dev/null || true' EXIT
        "$PROJECT_ROOT/.venv/bin/uvicorn" src.main:app --host 0.0.0.0 --port 8000 &
        sleep 2
        cd "$PROJECT_ROOT/bridges/whatsapp"
        node bridge.js
        ;;
    *)
        echo "Usage: ./run_bot.sh [all|backend|wa-bridge]"
        exit 1
        ;;
esac
