"""
Network Monitor - Einstiegspunkt
===============================
Liest Konfiguration, prüft alle Geräte, erstellt Reports und Plots.

Verwendung:
    python main.py                     # Einmaliger Scan + Plots
    python main.py --loop              # Dauerschleife (Intervall aus config.yaml)
    python main.py --no-plots          # Scan ohne Visualisierung
    python main.py --host 192.168.1.1 --ports 22 80 443

Autor : Portfolio-Projekt Network Monitor (FISI-Säule)
Standards : PEP 8, Clean Architecture
"""

import argparse
import logging
import sys
import time
from pathlib import Path

import yaml

# Eigene Module
try:
    from monitor import check_device
    from reporter import save_json_log, save_html_report
    # Visualizer wird am Anfang geladen, um Laufzeitfehler in der Loop zu vermeiden
    from visualizer import generate_all_plots
except ImportError as e:
    print(f"Fehler beim Laden der Monitor-Module: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("NetworkMonitor")


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def load_config(path: Path) -> dict:
    """Lädt die YAML-Konfigurationsdatei sicher.

    Returns
    -------
    dict
        Konfigurationsdaten oder leeres Dict bei Fehler.
    """
    if not path.exists():
        logger.error("Konfigurationsdatei nicht gefunden: %s", path)
        return {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.error("Fehler beim Parsen der YAML-Konfig: %s", e)
        return {}


def run_scan(devices: list[dict], skip_plots: bool = False) -> None:
    """Führt einen Scan durch und speichert die Ergebnisse.

    Parameters
    ----------
    devices : list[dict]
        Liste der zu prüfenden Geräte.
    skip_plots : bool, optional
        Ob die Visualisierung übersprungen werden soll.
    """
    logger.info("=" * 60)
    logger.info("  Network Monitor - Scan gestartet (%d Geräte)", len(devices))
    logger.info("=" * 60)

    results = []
    for device in devices:
        host = device.get("host")
        if not host:
            continue
            
        ports = device.get("ports", [22, 80, 443])
        result = check_device(host=host, ports=ports)
        results.append(result)

    # Reporting
    try:
        json_path = save_json_log(results)
        html_path = save_html_report(results)
        
        if not skip_plots:
            generate_all_plots()

        # Statistik
        stats = {"ONLINE": 0, "OFFLINE": 0, "DEGRADED": 0}
        for r in results:
            stats[r.status] = stats.get(r.status, 0) + 1

        logger.info("-" * 60)
        logger.info("  Status: ONLINE: %d | DEGRADED: %d | OFFLINE: %d", 
                    stats["ONLINE"], stats["DEGRADED"], stats["OFFLINE"])
        logger.info("  Berichte erstellt: %s, %s", json_path, html_path)
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("Fehler beim Erstellen der Reports: %s", e)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Network Monitor - Netzwerk-Überwachung")
    parser.add_argument("--loop",     action="store_true", help="Dauerschleife aktiv")
    parser.add_argument("--no-plots", action="store_true", help="Keine Plots erstellen")
    parser.add_argument("--host",     type=str,            help="Einzelnen Host prüfen")
    parser.add_argument("--ports",    type=int, nargs="+", default=[22, 80, 443])
    parser.add_argument("--config",   type=str,            default="config.yaml")
    args = parser.parse_args()

    # Szenario A: Einzelner Host-Check
    if args.host:
        logger.info("Einzelprüfung für Host: %s", args.host)
        result = check_device(args.host, args.ports)
        save_json_log([result])
        save_html_report([result])
        if not args.no_plots:
            generate_all_plots()
        return

    # Szenario B: Konfigurationsbasierter Scan
    config_path = Path(args.config)
    config   = load_config(config_path)
    devices  = config.get("devices", [])
    interval = config.get("scan_interval_seconds", 60)

    if not devices:
        logger.warning("Keine Geräte in der Konfiguration gefunden. Ende.")
        return

    if args.loop:
        logger.info("Monitoring-Modus gestartet (Intervall: %ds).", interval)
        try:
            while True:
                run_scan(devices, skip_plots=args.no_plots)
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("\nMonitoring durch Benutzer beendet. Fahre sauber herunter...")
    else:
        run_scan(devices, skip_plots=args.no_plots)
        logger.info("Einmaliger Scan abgeschlossen.")


if __name__ == "__main__":
    main()
