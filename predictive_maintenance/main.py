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
from pathlib import Path

from data_generator import generate_sensor_data, save_raw_data
from pipeline import run_pipeline
from anomaly_detection import run_anomaly_detection
from visualization import generate_all_plots

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Verarbeitet Kommandozeilenargumente.

    Returns
    -------
    argparse.Namespace
        Geparste Argumente.
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
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Orchestriert die gesamte Predictive-Maintenance-Pipeline."""
    args = parse_args()

    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║  Predictive Maintenance Pipeline             ║")
    logger.info("║  Medizintechnik-Fertigungsumgebung           ║")
    logger.info("╚══════════════════════════════════════════════╝")
    logger.info("Parameter: samples=%d | anomaly_rate=%.2f | seed=%d",
                args.samples, args.anomaly_rate, args.seed)

    # 1. Rohdaten generieren
    logger.info("--- Schritt 1/4: Rohdaten generieren ---")
    df_raw = generate_sensor_data(
        n_samples=args.samples,
        anomaly_rate=args.anomaly_rate,
        seed=args.seed,
    )
    save_raw_data(df_raw, args.data_dir)

    # 2. Pipeline (bereinigen + Feature Engineering)
    logger.info("--- Schritt 2/4: Datenpipeline ---")
    df_processed = run_pipeline(
        raw_path=args.data_dir / "raw_sensor_data.csv",
        output_dir=args.data_dir,
    )

    # 3. Anomalieerkennung
    logger.info("--- Schritt 3/4: Anomalieerkennung ---")
    df_scored = run_anomaly_detection(df_processed)
    out_path = args.data_dir / "anomaly_scores.csv"
    df_scored.to_csv(out_path, index=False)
    logger.info("Anomalie-Scores gespeichert: %s", out_path)

    # 4. Visualisierungen
    logger.info("--- Schritt 4/4: Visualisierungen ---")
    plots = generate_all_plots(df_scored)
    logger.info("%d Plots erstellt in: docs/plots/", len(plots))

    logger.info("✓ Pipeline erfolgreich abgeschlossen.")


if __name__ == "__main__":
    main()
