"""
data_generator.py
=================
Simuliert Rohdaten von Produktionsmaschinen (z. B. Injektionsformmaschinen,
Autoklave-Sterilisatoren) wie sie in der medizintechnischen Fertigung
in der medizintechnischen Fertigungsindustrie vorkommen.

Erzeugte Signale:
    - Temperatur (°C)         – Heizzonen, Motorlager
    - Vibration (mm/s)        – Spindeln, Pumpen
    - Druck (bar)             – Hydraulik, Pneumatik
    - Zykluszeit (s)          – Prozessüberwachung
    - Betriebsstunden (h)     – Verschleißindikator

Anomalien werden probabilistisch eingefügt, um realistische Degradation
(Lagerverschleiß, Dichtungsverlust) nachzubilden.

Autor : Portfolio-Projekt Predictive Maintenance
PEP 8 : Ja
"""

import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
SENSOR_COLUMNS = [
    "timestamp",
    "machine_id",
    "temperature_c",
    "vibration_mm_s",
    "pressure_bar",
    "cycle_time_s",
    "operating_hours",
    "label",          # 0 = normal, 1 = anomalie
]

MACHINES = ["MED-INJ-01", "MED-INJ-02", "MED-AUTO-01", "MED-PUMP-01"]

# Normalverteilung der Basiswerte pro Sensor
BASE_PARAMS: dict[str, dict] = {
    "temperature_c":  {"mean": 65.0,  "std": 2.0},
    "vibration_mm_s": {"mean": 1.2,   "std": 0.15},
    "pressure_bar":   {"mean": 6.5,   "std": 0.3},
    "cycle_time_s":   {"mean": 12.0,  "std": 0.5},
}

# Faktor-Bereich für simulierte Anomalien
ANOMALY_FACTOR = (1.4, 2.2)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _generate_sample(
    machine_id: str,
    timestamp: datetime,
    operating_hours: float,
    anomaly: bool = False,
) -> dict:
    """Erzeugt einen einzelnen Sensordatensatz.

    Parameters
    ----------
    machine_id : str
        Bezeichner der Maschine.
    timestamp : datetime
        Aufnahmezeitpunkt.
    operating_hours : float
        Kumulierte Betriebsstunden der Maschine.
    anomaly : bool, optional
        Falls True, werden die Sensorwerte mit einem Zufallsfaktor
        außerhalb des Normalbereichs skaliert (Default: False).

    Returns
    -------
    dict
        Sensor-Datensatz als Dictionary.
    """
    factor = random.uniform(*ANOMALY_FACTOR) if anomaly else 1.0

    row: dict = {"timestamp": timestamp, "machine_id": machine_id}

    for sensor, params in BASE_PARAMS.items():
        value = np.random.normal(params["mean"], params["std"]) * factor
        # Physikalisch sinnvolle Untergrenze
        row[sensor] = max(0.0, round(value, 3))

    row["operating_hours"] = round(operating_hours, 1)
    row["label"] = int(anomaly)
    return row


def generate_sensor_data(
    n_samples: int = 5_000,
    anomaly_rate: float = 0.05,
    start_time: Optional[datetime] = None,
    interval_seconds: int = 60,
    seed: int = 42,
) -> pd.DataFrame:
    """Generiert einen synthetischen Sensor-Datensatz.

    Die Funktion verteilt Messungen gleichmäßig über alle Maschinen
    in ``MACHINES``. Anomalien werden zufällig mit Wahrscheinlichkeit
    ``anomaly_rate`` eingefügt.

    Parameters
    ----------
    n_samples : int
        Gesamtzahl der Datensätze (Default: 5 000).
    anomaly_rate : float
        Anteil anomaler Messungen [0, 1] (Default: 0.05 = 5 %).
    start_time : datetime, optional
        Startzeitpunkt der Zeitreihe (Default: jetzt − n_samples Minuten).
    interval_seconds : int
        Zeitabstand zwischen zwei Messungen in Sekunden (Default: 60).
    seed : int
        Random Seed für Reproduzierbarkeit (Default: 42).

    Returns
    -------
    pd.DataFrame
        DataFrame mit Spalten gemäß ``SENSOR_COLUMNS``.

    Examples
    --------
    >>> df = generate_sensor_data(n_samples=100, seed=0)
    >>> len(df)
    100
    """
    np.random.seed(seed)
    random.seed(seed)

    if start_time is None:
        start_time = datetime(2024, 1, 1, 0, 0, 0)

    records = []
    op_hours: dict[str, float] = {m: random.uniform(500, 5_000) for m in MACHINES}

    for i in range(n_samples):
        machine = MACHINES[i % len(MACHINES)]
        ts = start_time + timedelta(seconds=i * interval_seconds)
        is_anomaly = random.random() < anomaly_rate
        op_hours[machine] += interval_seconds / 3_600  # Stunden aufaddieren
        records.append(_generate_sample(machine, ts, op_hours[machine], is_anomaly))

    df = pd.DataFrame(records, columns=SENSOR_COLUMNS)
    logger.info(
        "Datensatz erzeugt: %d Zeilen | %d Anomalien (%.1f %%)",
        len(df),
        df["label"].sum(),
        df["label"].mean() * 100,
    )
    return df


# ---------------------------------------------------------------------------
# Pipeline-Schritt: Rohdaten speichern
# ---------------------------------------------------------------------------

def save_raw_data(df: pd.DataFrame, output_dir: Path = Path("data")) -> Path:
    """Speichert den generierten Datensatz als CSV im Rohformat.

    Parameters
    ----------
    df : pd.DataFrame
        Zu speichernder Datensatz.
    output_dir : Path
        Zielverzeichnis (wird ggf. angelegt).

    Returns
    -------
    Path
        Pfad zur gespeicherten Datei.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / "raw_sensor_data.csv"
    df.to_csv(filepath, index=False)
    logger.info("Rohdaten gespeichert: %s", filepath.resolve())
    return filepath


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    df = generate_sensor_data()
    save_raw_data(df)
