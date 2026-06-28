#!/bin/bash
# China Pinginsider — local preview server
# Usage: ./serve.sh [port]

PORT=${1:-8080}
echo "🏓🐧 China Pinginsider — Preview Server"
echo "→ http://localhost:${PORT}"
echo "→ Ctrl+C to stop"
echo ""
cd "$(dirname "$0")/website" && python3 -m http.server "$PORT"
