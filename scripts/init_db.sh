#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"
"${PYTHON_BIN}" data/init_db.py "$@"
