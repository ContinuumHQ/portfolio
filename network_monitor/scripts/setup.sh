#!/usr/bin/env bash
# setup.sh – Automatische Installation und Start des Network Monitors
# Getestet auf: Arch Linux
# Verwendung: chmod +x setup.sh && sudo ./setup.sh

set -euo pipefail

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "======================================================"
echo "  Network Monitor – Automatische Installation"
echo "======================================================"
echo ""

# Root-Check
if [[ $EUID -ne 0 ]]; then
  fail "Dieses Skript muss als root ausgeführt werden (sudo ./setup.sh)"
fi

# Python prüfen
if ! command -v python3 &>/dev/null; then
  warn "Python3 nicht gefunden – wird installiert..."
  sudo pacman -S --noconfirm python python-pip iputils
else
  log "Python3 gefunden: $(python3 --version)"
fi

# pip prüfen
if ! command -v pip3 &>/dev/null; then
  sudo pacman -S --noconfirm python-pip
fi

# Abhängigkeiten installieren
log "Installiere Python-Abhängigkeiten..."
pip3 install -r requirements.txt --break-system-packages -q
log "Abhängigkeiten installiert"

# Docs-Verzeichnis
mkdir -p docs
log "Report-Verzeichnis: ./docs"

# Systemd Service (optional)
read -rp "Als systemd-Service installieren? (dauerhafter Hintergrunddienst) [j/N] " install_service
if [[ "${install_service,,}" == "j" ]]; then
  WORKDIR=$(pwd)
  PYTHON=$(which python3)

  cat > /etc/systemd/system/network-monitor.service <<EOF
[Unit]
Description=Network Monitor – Netzwerküberwachung
After=network.target

[Service]
Type=simple
WorkingDirectory=${WORKDIR}
ExecStart=${PYTHON} main.py --loop
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable network-monitor
  systemctl start network-monitor
  log "Service installiert und gestartet"
  log "Status: systemctl status network-monitor"
  log "Logs:   journalctl -u network-monitor -f"
else
  warn "Kein systemd-Service installiert. Manueller Start: python3 main.py"
fi

echo ""
echo "======================================================"
echo "  Installation abgeschlossen!"
echo "  Einmaliger Scan:   python3 main.py"
echo "  Dauerschleife:     python3 main.py --loop"
echo "  Docker:            docker-compose up -d"
echo "======================================================"
echo ""
