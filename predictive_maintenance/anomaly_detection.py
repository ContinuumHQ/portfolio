"""
anomaly_detection.py
====================
Statistisches Anomalie-Scoring für Sensordaten.

Zwei komplementäre Methoden
----------------------------
**Z-Score**
    Misst, wie viele Standardabweichungen ein Wert vom Mittelwert entfernt
    liegt.  Vorteil: intuitiv interpretierbar, reagiert schnell auf punktuelle
    Ausreißer. Nachteil: sensitiv gegenüber Extremwerten im Trainingsdatensatz,
    weil Mittelwert und Standardabweichung selbst durch Ausreißer verzerrt
    werden.

**IQR (Interquartilsabstand)**
    Definiert den Normalbereich als [Q1 − 1.5·IQR, Q3 + 1.5·IQR].  Vorteil:
    robust gegenüber Extremwerten, da Quartile nicht durch einzelne Spikes
    beeinflusst werden.  Ideal für den Einsatz in der Produktion, wo einzelne
    Messausreißer (Sensor-Rauschen) häufig sind.

Gemeinsam ergeben beide Methoden ein zuverlässigeres Signal als jede
Methode für sich: Ein Messpunkt gilt als Anomalie, wenn *mindestens eine*
Methode anschlägt.  Diese Kombination reduziert Fehlalarme (False Positives)
bei gleichzeitig hoher Sensitivität.

Autor : Portfolio-Projekt Predictive Maintenance
PEP 8 : Ja
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Schwellenwert Z-Score (Standardwert: 3 Sigma-Regel)
Z_THRESHOLD = 3.0

# Multiplikator für IQR-Methode (Standardwert nach Tukey)
IQR_MULTIPLIER = 1.5

# Sensorspalten, die in die Anomalieerkennung einfließen
SENSOR_COLS = [
    "temperature_c",
    "vibration_mm_s",
    "pressure_bar",
    "cycle_time_s",
]


# ---------------------------------------------------------------------------
# Z-Score
# ---------------------------------------------------------------------------

def compute_z_scores(df: pd.DataFrame, cols: list[str] = SENSOR_COLS) -> pd.DataFrame:
    """Berechnet den Z-Score für jede Sensorspalte.

    Der Z-Score wird pro Maschine separat berechnet, da unterschiedliche
    Maschinen verschiedene Baselines haben können (z. B. unterschiedliche
    Heizzonen-Temperaturen).

    Parameters
    ----------
    df : pd.DataFrame
        Eingabedatensatz mit Spalte ``machine_id``.
    cols : list[str]
        Spalten, für die der Z-Score berechnet werden soll.

    Returns
    -------
    pd.DataFrame
        Datensatz mit zusätzlichen ``<col>_zscore``-Spalten.
    """
    df = df.copy()
    for col in cols:
        grp = df.groupby("machine_id")[col]
        df[f"{col}_zscore"] = (
            (df[col] - grp.transform("mean")) / grp.transform("std").replace(0, np.nan)
        ).fillna(0)
    logger.debug("Z-Scores berechnet für: %s", cols)
    return df


def flag_zscore_anomalies(
    df: pd.DataFrame,
    cols: list[str] = SENSOR_COLS,
    threshold: float = Z_THRESHOLD,
) -> pd.DataFrame:
    """Markiert Zeilen, bei denen mindestens ein Z-Score den Schwellenwert übersteigt.

    Parameters
    ----------
    df : pd.DataFrame
        Datensatz mit berechneten Z-Score-Spalten.
    cols : list[str]
        Basis-Sensorspalten (ohne ``_zscore``-Suffix).
    threshold : float
        Grenzwert (Default: 3.0).

    Returns
    -------
    pd.DataFrame
        Datensatz mit neuer Spalte ``anomaly_zscore`` (bool).
    """
    df = df.copy()
    zscore_cols = [f"{c}_zscore" for c in cols]
    df["anomaly_zscore"] = (df[zscore_cols].abs() > threshold).any(axis=1)
    n = df["anomaly_zscore"].sum()
    logger.info("Z-Score-Anomalien: %d (%.2f %%)", n, n / len(df) * 100)
    return df


# ---------------------------------------------------------------------------
# IQR
# ---------------------------------------------------------------------------

def compute_iqr_bounds(
    df: pd.DataFrame,
    cols: list[str] = SENSOR_COLS,
    multiplier: float = IQR_MULTIPLIER,
) -> dict[str, dict[str, float]]:
    """Berechnet IQR-Grenzen pro Sensor (global, maschinenübergreifend).

    Die Grenzen werden global berechnet, um eine einheitliche Referenz
    für alle Maschinen zu erhalten.  In der Praxis könnten maschinenspezifische
    Grenzen sinnvoller sein — dies ist ein möglicher Erweiterungspunkt.

    Parameters
    ----------
    df : pd.DataFrame
        Datensatz.
    cols : list[str]
        Zu analysierende Spalten.
    multiplier : float
        IQR-Multiplikator (Default: 1.5 nach Tukey).

    Returns
    -------
    dict
        ``{sensor: {"lower": float, "upper": float}}``
    """
    bounds: dict[str, dict[str, float]] = {}
    for col in cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        bounds[col] = {
            "lower": q1 - multiplier * iqr,
            "upper": q3 + multiplier * iqr,
        }
        logger.debug(
            "IQR %s: Q1=%.3f, Q3=%.3f, IQR=%.3f → [%.3f, %.3f]",
            col, q1, q3, iqr, bounds[col]["lower"], bounds[col]["upper"],
        )
    return bounds


def flag_iqr_anomalies(
    df: pd.DataFrame,
    bounds: dict[str, dict[str, float]],
    cols: list[str] = SENSOR_COLS,
) -> pd.DataFrame:
    """Markiert Zeilen, die außerhalb der IQR-Grenzen liegen.

    Parameters
    ----------
    df : pd.DataFrame
        Eingabedatensatz.
    bounds : dict
        Ausgabe von :func:`compute_iqr_bounds`.
    cols : list[str]
        Zu prüfende Sensorspalten.

    Returns
    -------
    pd.DataFrame
        Datensatz mit neuer Spalte ``anomaly_iqr`` (bool).
    """
    df = df.copy()
    masks = pd.DataFrame(index=df.index)
    for col in cols:
        lo = bounds[col]["lower"]
        hi = bounds[col]["upper"]
        masks[col] = (df[col] < lo) | (df[col] > hi)

    df["anomaly_iqr"] = masks.any(axis=1)
    n = df["anomaly_iqr"].sum()
    logger.info("IQR-Anomalien: %d (%.2f %%)", n, n / len(df) * 100)
    return df


# ---------------------------------------------------------------------------
# Kombiniertes Scoring
# ---------------------------------------------------------------------------

def combined_anomaly_score(df: pd.DataFrame) -> pd.DataFrame:
    """Kombiniert Z-Score und IQR zu einem gemeinsamen Anomalie-Flag.

    Ein Datenpunkt gilt als Anomalie, wenn *mindestens eine* der beiden
    Methoden anschlägt.  Diese konservative OR-Verknüpfung erhöht die
    Sensitivität (weniger verpasste Anomalien), kann aber die Präzision
    leicht verringern — ein akzeptabler Trade-off in sicherheitskritischen
    Produktionsumgebungen, wo ein verpasster Defekt teurer ist als ein
    Fehlalarm.

    Parameters
    ----------
    df : pd.DataFrame
        Datensatz mit Spalten ``anomaly_zscore`` und ``anomaly_iqr``.

    Returns
    -------
    pd.DataFrame
        Datensatz mit neuer Spalte ``anomaly_combined`` (bool).
    """
    df = df.copy()
    df["anomaly_combined"] = df["anomaly_zscore"] | df["anomaly_iqr"]
    n = df["anomaly_combined"].sum()
    logger.info("Kombinierte Anomalien: %d (%.2f %%)", n, n / len(df) * 100)
    return df


# ---------------------------------------------------------------------------
# Convenience-Funktion
# ---------------------------------------------------------------------------

def run_anomaly_detection(df: pd.DataFrame) -> pd.DataFrame:
    """Führt die gesamte Anomalieerkennung in einem Schritt aus.

    Parameters
    ----------
    df : pd.DataFrame
        Bereinigter und feature-engineerter Datensatz.

    Returns
    -------
    pd.DataFrame
        Datensatz mit allen Anomalie-Flags und Z-Score-Spalten.
    """
    df = compute_z_scores(df)
    df = flag_zscore_anomalies(df)
    bounds = compute_iqr_bounds(df)
    df = flag_iqr_anomalies(df, bounds)
    df = combined_anomaly_score(df)
    return df


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    from pipeline import run_pipeline  # noqa: PLC0415

    df_processed = run_pipeline()
    df_scored = run_anomaly_detection(df_processed)
    out = Path("data/anomaly_scores.csv")
    df_scored.to_csv(out, index=False)
    logger.info("Anomalie-Scores gespeichert: %s", out)
