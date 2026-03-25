"""
Sales Dashboard – Einstiegspunkt
===============================
Initialisiert DB, generiert Daten, erstellt Plots und exportiert Reports.

Verwendung:
    python main.py                  # Vollständiger Durchlauf
    python main.py --no-plots       # Nur DB + Export, keine Plots
    python main.py --export-only    # Nur Exports (DB muss vorhanden sein)
    python main.py --records 5000   # Mehr Testdaten generieren

Autor : Portfolio-Projekt Sales Dashboard (FIDP-Säule)
Standards : PEP 8, SQL-Integration, Excel-Automation
"""

import argparse
import logging
import sys
from pathlib import Path

# Eigene Module (Vorab-Check für saubere Architektur)
try:
    from database import init_db, get_connection
    from data_seeder import generate_sales
    from visualizations import generate_all_plots
    from exporter import export_csv, export_excel
except ImportError as e:
    print(f"Fehler beim Laden der Dashboard-Module: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SalesDashboard")


# ---------------------------------------------------------------------------
# Kern-Logik
# ---------------------------------------------------------------------------

def run_database_setup(records: int, seed: int) -> None:
    """Initialisiert die Datenbank und füllt sie bei Bedarf mit Daten."""
    logger.info("Schritt 1: Datenbank-Integrität prüfen...")
    init_db()
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Prüfen, ob Tabelle existiert und Daten hat
            cursor.execute("SELECT COUNT(*) FROM sales")
            count = cursor.fetchone()[0]

            if count == 0:
                logger.info("Datenbank leer. Generiere %d neue Datensätze (Seed: %d)...", records, seed)
                generate_sales(n=records, seed=seed)
            else:
                logger.info("Datenbank enthält bereits %d Datensätze. Überspringe Seeding.", count)
    except Exception as e:
        logger.error("Fehler beim Datenbank-Setup: %s", e)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Sales Dashboard – Datenanalyse & Reporting")
    parser.add_argument("--no-plots",    action="store_true", help="Keine Visualisierungen erstellen")
    parser.add_argument("--export-only", action="store_true", help="Nur Exports (überspringt DB-Setup)")
    parser.add_argument("--records",     type=int, default=2000, help="Anzahl synthetischer Verkäufe")
    parser.add_argument("--seed",        type=int, default=42, help="Zufallsseed für Reproduzierbarkeit")
    args = parser.parse_args()

    # Sicherstellen, dass Export-Verzeichnisse existieren
    Path("docs/reports").mkdir(parents=True, exist_ok=True)
    Path("docs/plots").mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("  Sales Dashboard – Business Intelligence Pipeline")
    logger.info("=" * 60)

    try:
        # 1. Datenbank & Daten-Generierung
        if not args.export_only:
            run_database_setup(args.records, args.seed)
        else:
            logger.info("Modus: --export-only aktiv. Bestehende Datenbank wird genutzt.")

        # 2. Visualisierung
        if not args.no_plots:
            logger.info("Schritt 2: Generiere Analyse-Plots...")
            plot_paths = generate_all_plots()
            logger.info("  ✓ %d Plots erstellt.", len(plot_paths))
        else:
            logger.info("Schritt 2: Visualisierung übersprungen (--no-plots).")

        # 3. Export
        logger.info("Schritt 3: Daten-Export (CSV & Excel)...")
        csv_path = export_csv()
        excel_path = export_excel()

        logger.info("-" * 60)
        logger.info("  Analyse erfolgreich abgeschlossen.")
        logger.info("  Bericht (CSV):   %s", csv_path)
        logger.info("  Bericht (Excel): %s", excel_path)
        logger.info("=" * 60)

    except Exception as e:
        logger.error("Kritischer Fehler in der Dashboard-Pipeline: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
