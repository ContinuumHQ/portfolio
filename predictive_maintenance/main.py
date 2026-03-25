"""
main.py
=======
Einstiegspunkt für das Predictive-Maintenance-Projekt.

Führt die komplette Verarbeitungskette aus:
    1. Rohdaten generieren  (data_generator)
    2. Pipeline ausführen   (pipeline)
    3. Anomalien erkennen   (anomaly_detection)
    4. Visualisierungen     (visualization)

Verwendung
----------
    python main.py                  # Standardlauf (5 000 Samples)
    python main.py --samples 10000  # Mehr Datenpunkte
    python main.py --anomaly-rate 0.08

Autor : Portfolio-Projekt Predictive Maintenance
PEP 8 : Ja
"""

import argparse
import logging
import sys
from pathlib import Path

# Eigene Module
try:
    from data_generator import generate_sensor_data, save_raw_data
    from pipeline import run_pipeline
    from anomaly_detection import run_anomaly_detection
    from visualization import generate_all_plots
except ImportError as e:
    print(f"Fehler beim Importieren der Projektmodule: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Logging-Konfiguration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CLI-Schnittstelle
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Verarbeitet Kommandozeilenargumente.

    Returns
    -------
    argparse.Namespace
        Geparste Argumente für die Pipeline-Steuerung.
    """
    parser = argparse.ArgumentParser(
        description="Predictive Maintenance – Vollständige Analysepipeline"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=5_000,
        help="Anzahl der zu generierenden Datenpunkte (Default: 5000)",
    )
    parser.add_argument(
        "--anomaly-rate",
        type=float,
        default=0.05,
        help="Anteil anomaler Messungen [0, 1] (Default: 0.05)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random Seed für Reproduzierbarkeit (Default: 42)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Verzeichnis für Roh- und Prozessdaten (Default: data/)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Orchestrierung (Main)
# ---------------------------------------------------------------------------

def main() -> None:
    """Orchestriert die gesamte Predictive-Maintenance-Pipeline."""
    args = parse_args()

    # Vorbereitung: Verzeichnisse sicherstellen
    raw_data_path = args.data_dir / "raw_sensor_data.csv"
    processed_out_path = args.data_dir / "anomaly_scores.csv"
    plot_dir = Path("docs") / "plots"

    try:
        args.data_dir.mkdir(parents=True, exist_ok=True)
        plot_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error("Konnte Verzeichnisstruktur nicht erstellen: %s", e)
        sys.exit(1)

    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║   Predictive Maintenance Pipeline            ║")
    logger.info("║   Medizintechnik-Fertigungsumgebung          ║")
    logger.info("╚══════════════════════════════════════════════╝")
    logger.info("Parameter: samples=%d | anomaly_rate=%.2f | seed=%d",
                args.samples, args.anomaly_rate, args.seed)

    try:
        # 1. Rohdaten generieren
        logger.info("--- Schritt 1/4: Rohdaten generieren ---")
        df_raw = generate_sensor_data(
            n_samples=args.samples,
            anomaly_rate=args.anomaly_rate,
            seed=args.seed,
        )
        save_raw_data(df_raw, args.data_dir)
        logger.info("Rohdaten erfolgreich erstellt.")

        # 2. Pipeline (bereinigen + Feature Engineering)
        logger.info("--- Schritt 2/4: Datenpipeline ---")
        df_processed = run_pipeline(
            raw_path=raw_data_path,
            output_dir=args.data_dir,
        )

        # 3. Anomalieerkennung
        logger.info("--- Schritt 3/4: Anomalieerkennung ---")
        df_scored = run_anomaly_detection(df_processed)
        df_scored.to_csv(processed_out_path, index=False)
        logger.info("Anomalie-Scores gespeichert: %s", processed_out_path)

        # 4. Visualisierungen
        logger.info("--- Schritt 4/4: Visualisierungen ---")
        plots = generate_all_plots(df_scored)
        logger.info("✓ %d Plots erstellt in: %s", len(plots), plot_dir)

        logger.info("✅ Pipeline erfolgreich abgeschlossen.")

    except FileNotFoundError as fnf:
        logger.error("Datei nicht gefunden: %s", fnf)
        sys.exit(1)
    except Exception as e:
        logger.error("Kritischer Fehler während der Pipeline-Ausführung: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
