#!/usr/bin/env bash
# Annotation Cycle — サーバー起動・ブラウザ表示・イベント待機
#
# Usage:
#   annotation-cycle.sh --feature <feature-name> [--wait-only]
#   annotation-cycle.sh --stop
#
# --wait-only: サーバー起動・ブラウザ表示をスキップし、ポーリングのみ行う
#              （コメント修正後の再待機に使用）
# --stop: サーバーを停止する
#
# 出力（stdout）:
#   PORT:{port}           — サーバーのポート番号（--wait-only 時は出力しない）
#   COMMENTS_SAVED        — コメントが送信された
#   REVIEW_DONE           — レビューが完了した

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_SCRIPT="${SCRIPT_DIR}/annotation-viewer/server.py"
SIGNAL_DIR="/tmp/spec-flow-review"
LOCK_FILE="/tmp/annotation-viewer.lock"

# ─── Parse args ───

FEATURE=""
WAIT_ONLY=false
STOP=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --feature)   FEATURE="$2"; shift 2 ;;
        --wait-only) WAIT_ONLY=true; shift ;;
        --stop)      STOP=true; shift ;;
        *)           echo "Error: Unknown option: $1" >&2; exit 1 ;;
    esac
done

# ─── Stop server ───

if [[ "$STOP" == true ]]; then
    if [[ -f "$LOCK_FILE" ]]; then
        PORT="$(python3 -c "import json; d=json.load(open('$LOCK_FILE')); print(d.get('port',''))" 2>/dev/null || true)"
        if [[ -n "$PORT" ]]; then
            curl -s -X POST "http://127.0.0.1:${PORT}/api/shutdown" >/dev/null 2>&1 || true
        fi
        # Fallback: kill by PID if shutdown API failed
        PID="$(python3 -c "import json; d=json.load(open('$LOCK_FILE')); print(d.get('pid',''))" 2>/dev/null || true)"
        sleep 1
        if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null || true
        fi
        rm -f "$LOCK_FILE"
    fi
    echo "Server stopped"
    exit 0
fi

[[ -n "$FEATURE" ]] || { echo "Error: --feature is required" >&2; exit 1; }

FEATURE_DIR="${SIGNAL_DIR}/${FEATURE}"

# ─── Helper: read port from lock file ───

read_lock_port() {
    python3 -c "import json; d=json.load(open('$LOCK_FILE')); print(d.get('port',''))" 2>/dev/null || true
}

# ─── Helper: ensure server is running (lazy start) ───

ensure_server() {
    if [[ -f "$LOCK_FILE" ]]; then
        PORT="$(read_lock_port)"
        if [[ -n "$PORT" ]] && curl -s -o /dev/null -w '' "http://127.0.0.1:${PORT}/api/plans" 2>/dev/null; then
            # Server is running, register plan
            curl -s -X POST "http://127.0.0.1:${PORT}/api/plans/register" \
                -H "Content-Type: application/json" \
                -d "{\"feature\": \"${FEATURE}\"}" >/dev/null 2>&1 || true
            echo "$PORT"
            return
        fi
        # Lock file exists but server is dead
        rm -f "$LOCK_FILE"
    fi

    # Start new server in background
    PORT_FILE="$(mktemp)"
    python3 "$SERVER_SCRIPT" --feature "$FEATURE" > "$PORT_FILE" 2>/dev/null &

    # Wait for PORT line (max 10 seconds)
    PORT=""
    for _ in $(seq 1 20); do
        if [[ -s "$PORT_FILE" ]]; then
            PORT="$(grep -m1 '^PORT:' "$PORT_FILE" 2>/dev/null | sed 's/PORT://')"
            [[ -n "$PORT" ]] && break
        fi
        sleep 0.5
    done
    rm -f "$PORT_FILE"

    # Fallback: check lock file
    if [[ -z "$PORT" ]] && [[ -f "$LOCK_FILE" ]]; then
        PORT="$(read_lock_port)"
    fi

    echo "$PORT"
}

# ─── Start server + open browser ───

if [[ "$WAIT_ONLY" == false ]]; then
    # Clean up stale signal files
    rm -f "${FEATURE_DIR}/comments.json" "${FEATURE_DIR}/review-done.flag" 2>/dev/null

    PORT="$(ensure_server)"

    if [[ -z "$PORT" ]]; then
        echo "Error: Could not determine server port" >&2
        exit 1
    fi

    echo "PORT:${PORT}"

    # Open browser
    if command -v open &>/dev/null; then
        open "http://localhost:${PORT}"
    elif command -v xdg-open &>/dev/null; then
        xdg-open "http://localhost:${PORT}"
    fi
fi

# ─── Poll for events ───

while true; do
    if [[ -f "${FEATURE_DIR}/review-done.flag" ]]; then
        echo "REVIEW_DONE"
        exit 0
    fi

    if [[ -f "${FEATURE_DIR}/comments.json" ]]; then
        rm -f "${FEATURE_DIR}/comments.json"
        echo "COMMENTS_SAVED"
        exit 0
    fi

    sleep 3
done
