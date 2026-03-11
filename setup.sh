#!/bin/bash
# Setup docs-dashboard for any project
# Usage: ./setup.sh /path/to/project/docs [project-name] [port]

set -e

DOCS_PATH="${1:?Usage: ./setup.sh /path/to/project/docs [project-name] [port]}"
PROJECT_NAME="${2:-$(basename "$(dirname "$(cd "$DOCS_PATH" && pwd)")")}"
PORT="${3:-15000}"

# Resolve to absolute path
DOCS_PATH="$(cd "$DOCS_PATH" && pwd)"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cat > "$SCRIPT_DIR/.env" << EOF
DOCS_PATH=${DOCS_PATH}
PROJECT_NAME=${PROJECT_NAME}
PORT=${PORT}
EOF

echo "docs-dashboard configured:"
echo "  DOCS_PATH     = ${DOCS_PATH}"
echo "  PROJECT_NAME  = ${PROJECT_NAME}"
echo "  PORT          = ${PORT}"
echo ""
echo "Next: cd $(basename "$SCRIPT_DIR") && docker compose up -d --build"
echo "Open: http://localhost:${PORT}"
