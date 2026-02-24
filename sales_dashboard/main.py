"""
Sales Dashboard – Einstiegspunkt
Initialisiert DB, generiert Daten, erstellt Plots und exportiert Reports.

Verwendung:
    python main.py                  # Vollständiger Durchlauf
    python main.py --no-plots       # Nur DB + Export, keine Plots
    python main.py --export-only    # Nur Exports (DB muss vorhanden sein)
    python main.py --records 5000   # Mehr Testdaten generieren
"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sales Dashboard – Datenanalyse & Reporting")
    parser.add_argument("--no-plots",    action="store_true", help="Keine Visualisierungen erstellen")
    parser.add_argument("--export-only", action="store_true", help="Nur Exports (überspring DB-Setup)")
    parser.add_argument("--records",     type=int, default=2000, help="Anzahl synthetischer Verkäufe")
    parser.add_argument("--seed",        type=int, default=42, help="Zufallsseed")
    args = parser.parse_args()

    logger.info("=" * 55)
    logger.info("  Sales Dashboard – Analyse gestartet")
    logger.info("=" * 55)

    if not args.export_only:
        from data_seeder import setup_demo_db, generate_sales
        from database import init_db, get_connection, DB_PATH

        init_db()
        with get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]

        if count == 0:
            generate_sales(n=args.records, seed=args.seed)
        else:
            logger.info("Datenbank enthält %d Datensätze – kein Re-Seed.", count)

    if not args.no_plots:
        from visualizations import generate_all_plots
        paths = generate_all_plots()
        for p in paths:
            logger.info("  Plot: %s", p)

    from exporter import export_csv, export_excel
    csv_path   = export_csv()
    excel_path = export_excel()

    logger.info("-" * 55)
    logger.info("  ✓ Dashboard abgeschlossen")
    logger.info("  CSV  : %s", csv_path)
    logger.info("  Excel: %s", excel_path)
    logger.info("=" * 55)


if __name__ == "__main__":
    main()
