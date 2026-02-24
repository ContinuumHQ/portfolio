#!/usr/bin/env bash
# Aktiviert die Portfolio-venv — einfach ausführen mit: source aktivieren.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
echo "✓ Portfolio-venv aktiv: $(python --version)"
echo "  Deaktivieren mit: deactivate"
