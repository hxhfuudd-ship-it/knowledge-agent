#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/knowledge-agent-pyc}"

"${PYTHON_BIN}" -m compileall -q src tests app.py import_csv.py mcp_servers data/init_db.py
"${PYTHON_BIN}" -m pytest -q "$@"
