#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="python3"
if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
  PYTHON="$SCRIPT_DIR/venv/bin/python"
fi

"$PYTHON" "$SCRIPT_DIR/set_theme.py" "$@"
