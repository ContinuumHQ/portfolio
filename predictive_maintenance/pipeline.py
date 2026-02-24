"""
pipeline.py
===========
Datenpipeline für Predictive-Maintenance-Rohdaten.

Verarbeitungsschritte
---------------------
1. **Laden**       – CSV einlesen, Typen validieren
2. **Bereinigen**  – Duplikate, fehlende Werte, Wertebereichsprüfung
3. **Feature Engineering** – rollierende Statistiken, Differenzen
4. **Exportieren** – bereinigten Datensatz speichern

Das Modul ist bewusst in einzelne, testbare Funktionen aufgeteilt
(Single-Responsibility-Prinzip), damit Änderungen an einem Schritt
die anderen nicht beeinflussen.

Autor : Portfolio-Projekt Predictive Maintenance
PEP 8 : Ja
"""

import logging
from pathlib import Path

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gültige Wertebereiche für die Plausibilitätsprüfung
# ---------------------------------------------------------------------------
VALUE_RANGES: dict[str, tuple[float, float]] = {
    "temperature_c":  (0.0,  200.0),
    "vibration_mm_s": (0.0,   50.0),
    "pressure_bar":   (0.0,   30.0),
    "cycle_time_s":   (0.1,  120.0),
    "operating_hours": (0.0, 100_000.0),
}

WINDOW_SIZE = 10  # Fenstergröße für rollierende Features (Messungen)


# ---------------------------------------------------------------------------
# Schritt 1 – Laden
# ---------------------------------------------------------------------------

def load_data(filepath: Path) -> pd.DataFrame:
    """Lädt CSV-Rohdaten und stellt korrekte Datentypen sicher.

    Parameters
    ----------
    filepath : Path
        Pfad zur CSV-Datei.

    Returns
    -------
    pd.DataFrame
        Datensatz mit geparsten Zeitstempeln und numerischen Spalten.

    Raises
    ------
    FileNotFoundError
        Wenn die Datei nicht existiert.
    ValueError
        Wenn Pflichtspalten fehlen.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {filepath}")

    df = pd.read_csv(filepath, parse_dates=["timestamp"])

    required = {"timestamp", "machine_id", "label"} | set(VALUE_RANGES.keys())
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Fehlende Spalten im Datensatz: {missing}")

    logger.info("Daten geladen: %d Zeilen, %d Spalten", *df.shape)
    return df


# ---------------------------------------------------------------------------
# Schritt 2 – Bereinigen
# ---------------------------------------------------------------------------

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Bereinigt den Datensatz in mehreren Teilschritten.

    Teilschritte:
    - Duplikate entfernen (gleicher Timestamp + Machine ID)
    - Fehlende Werte auffüllen (Forward Fill, dann Mittelwert)
    - Wertebereiche prüfen und Ausreißer kappen (Clipping)

    Parameters
    ----------
    df : pd.DataFrame
        Rohdatensatz.

    Returns
    -------
    pd.DataFrame
        Bereinigter Datensatz (Kopie).
    """
    df = df.copy()

    # --- Duplikate ---
    before = len(df)
    df.drop_duplicates(subset=["timestamp", "machine_id"], inplace=True)
    logger.info("Duplikate entfernt: %d Zeilen", before - len(df))

    # --- Fehlende Werte ---
    df.sort_values(["machine_id", "timestamp"], inplace=True)
    numeric_cols = list(VALUE_RANGES.keys())
    df[numeric_cols] = (
        df.groupby("machine_id")[numeric_cols]
        .transform(lambda s: s.ffill().bfill())
        .fillna(df[numeric_cols].mean())
    )

    # --- Plausibilitätsprüfung (Clipping statt Löschen) ---
    # Werte außerhalb des physikalisch sinnvollen Bereichs werden auf die
    # Grenzwerte gesetzt, damit keine Zeilen verloren gehen.
    for col, (lo, hi) in VALUE_RANGES.items():
        df[col] = df[col].clip(lower=lo, upper=hi)

    logger.info("Daten bereinigt: %d Zeilen verbleiben", len(df))
    return df


# ---------------------------------------------------------------------------
# Schritt 3 – Feature Engineering
# ---------------------------------------------------------------------------

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Erzeugt abgeleitete Merkmale für das Anomalie-Scoring.

    Neue Spalten pro numerischem Sensor:
    - ``<sensor>_roll_mean``  – Rollierender Mittelwert (Fenstergröße: WINDOW_SIZE)
    - ``<sensor>_roll_std``   – Rollierende Standardabweichung
    - ``<sensor>_diff``       – Erste Differenz (Änderungsrate)

    Die rollierende Standardabweichung ist besonders wertvoll: Ein plötzlicher
    Anstieg deutet auf instabiles Maschinenverhalten hin, bevor der Absolutwert
    den Normalbereich verlässt.

    Parameters
    ----------
    df : pd.DataFrame
        Bereinigter Datensatz.

    Returns
    -------
    pd.DataFrame
        Datensatz mit zusätzlichen Feature-Spalten.
    """
    df = df.copy().sort_values(["machine_id", "timestamp"])

    numeric_cols = list(VALUE_RANGES.keys())

    for col in numeric_cols:
        grp = df.groupby("machine_id")[col]
        df[f"{col}_roll_mean"] = grp.transform(
            lambda s: s.rolling(WINDOW_SIZE, min_periods=1).mean()
        )
        df[f"{col}_roll_std"] = grp.transform(
            lambda s: s.rolling(WINDOW_SIZE, min_periods=1).std().fillna(0)
        )
        df[f"{col}_diff"] = grp.transform(lambda s: s.diff().fillna(0))

    logger.info(
        "Feature Engineering abgeschlossen: %d Spalten total", len(df.columns)
    )
    return df


# ---------------------------------------------------------------------------
# Schritt 4 – Exportieren
# ---------------------------------------------------------------------------

def save_processed_data(df: pd.DataFrame, output_dir: Path = Path("data")) -> Path:
    """Speichert den verarbeiteten Datensatz als CSV.

    Parameters
    ----------
    df : pd.DataFrame
        Verarbeiteter Datensatz.
    output_dir : Path
        Zielverzeichnis.

    Returns
    -------
    Path
        Pfad zur gespeicherten Datei.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / "processed_sensor_data.csv"
    df.to_csv(filepath, index=False)
    logger.info("Verarbeitete Daten gespeichert: %s", filepath.resolve())
    return filepath


# ---------------------------------------------------------------------------
# Gesamte Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    raw_path: Path = Path("data/raw_sensor_data.csv"),
    output_dir: Path = Path("data"),
) -> pd.DataFrame:
    """Führt die komplette Datenpipeline aus.

    Kombiniert Laden → Bereinigen → Feature Engineering → Exportieren.

    Parameters
    ----------
    raw_path : Path
        Pfad zur Rohdaten-CSV.
    output_dir : Path
        Ausgabeverzeichnis für den verarbeiteten Datensatz.

    Returns
    -------
    pd.DataFrame
        Finaler Datensatz nach allen Pipeline-Schritten.
    """
    logger.info("=== Pipeline gestartet ===")
    df = load_data(raw_path)
    df = clean_data(df)
    df = engineer_features(df)
    save_processed_data(df, output_dir)
    logger.info("=== Pipeline abgeschlossen ===")
    return df


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    run_pipeline()
