"""
Network Monitor - Einstiegspunkt
Liest Konfiguration, prueft alle Geraete, erstellt Reports und Plots.

Verwendung:
    python main.py                     # Einmaliger Scan + Plots
    python main.py --loop              # Dauerschleife (Intervall aus config.yaml)
    python main.py --no-plots          # Scan ohne Visualisierung
    python main.py --host 192.168.1.1 --ports 22 80 443
"""

import argparse
import logging
import time
from pathlib import Path

import yaml

from monitor import check_device
from reporter import save_json_log, save_html_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def load_config(path: Path) -> dict:
    """Laedt die YAML-Konfigurationsdatei."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_scan(devices: list[dict]) -> None:
    """Fuehrt einen vollstaendigen Scan aller konfigurierten Geraete durch."""
    logger.info("=" * 55)
    logger.info("  Network Monitor - Scan gestartet")
    logger.info("  Geraete: %d", len(devices))
    logger.info("=" * 55)

    results = []
    for device in devices:
        result = check_device(
            host=device["host"],
            ports=device.get("ports", [22, 80, 443])
        )
        results.append(result)

    json_path = save_json_log(results)
    html_path = save_html_report(results)

    online   = sum(1 for r in results if r.status == "ONLINE")
    offline  = sum(1 for r in results if r.status == "OFFLINE")
    degraded = sum(1 for r in results if r.status == "DEGRADED")

    logger.info("-" * 55)
    logger.info("  Scan abgeschlossen")
    logger.info("  ONLINE: %d | DEGRADED: %d | OFFLINE: %d", online, degraded, offline)
    logger.info("  JSON : %s", json_path)
    logger.info("  HTML : %s", html_path)
    logger.info("=" * 55)


def main() -> None:
    parser = argparse.ArgumentParser(description="Network Monitor - Netzwerk-Ueberwachungstool")
    parser.add_argument("--loop",     action="store_true", help="Dauerschleife mit Intervall aus config.yaml")
    parser.add_argument("--no-plots", action="store_true", help="Keine Visualisierungen erstellen")
    parser.add_argument("--host",     type=str,            help="Einzelnen Host pruefen")
    parser.add_argument("--ports",    type=int, nargs="+", default=[22, 80, 443])
    parser.add_argument("--config",   type=str,            default="config.yaml")
    args = parser.parse_args()

    if args.host:
        result = check_device(args.host, args.ports)
        save_json_log([result])
        save_html_report([result])
        if not args.no_plots:
            from visualizer import generate_all_plots
            generate_all_plots()
        return

    config   = load_config(Path(args.config))
    devices  = config.get("devices", [])
    interval = config.get("scan_interval_seconds", 60)

    if args.loop:
        logger.info("Dauerschleife aktiv - Intervall: %d Sekunden (Ctrl+C zum Stoppen)", interval)
        while True:
            run_scan(devices)
            if not args.no_plots:
                from visualizer import generate_all_plots
                generate_all_plots()
            time.sleep(interval)
    else:
        run_scan(devices)
        if not args.no_plots:
            from visualizer import generate_all_plots
            generate_all_plots()


if __name__ == "__main__":
    main()
