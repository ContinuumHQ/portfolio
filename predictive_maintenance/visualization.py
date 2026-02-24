"""
visualization.py
================
Datenvisualisierung für das Predictive-Maintenance-Dashboard.

Erzeugte Plots
--------------
1. **Zeitreihe** – Sensorverlauf mit eingezeichneten Anomalien
2. **Z-Score-Heatmap** – Übersicht aller Sensoren und Maschinen
3. **IQR-Boxplots** – Verteilung pro Sensor, Normal vs. Anomalie
4. **Anomalie-Zeitlinie** – Kumulierte Anomaliezählung über die Zeit
5. **Korrelationsmatrix** – Zusammenhang der Sensorsignale

Warum Z-Score UND IQR visualisiert werden
------------------------------------------
- Der **Z-Score-Plot** zeigt, *wie weit* ein Wert vom Mittelwert abweicht —
  nützlich, um graduelle Degradation (schleichender Temperaturanstieg) zu
  erkennen, bevor ein harter Schwellenwert überschritten wird.
- Die **IQR-Boxplots** zeigen die Gesamtverteilung und machen deutlich,
  dass Ausreißer nicht symmetrisch um den Mittelwert liegen müssen —
  dies ist in der Praxis häufig der Fall (z. B. einseitiger Druckanstieg
  bei Leckage).

Autor : Portfolio-Projekt Predictive Maintenance
PEP 8 : Ja
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stil
# ---------------------------------------------------------------------------
sns.set_theme(style="darkgrid", palette="muted")
FIGSIZE_WIDE = (14, 5)
FIGSIZE_SQUARE = (10, 8)

OUTPUT_DIR = Path("docs/plots")

ANOMALY_COLOR = "#e74c3c"
NORMAL_COLOR = "#2ecc71"

SENSOR_LABELS: dict[str, str] = {
    "temperature_c":  "Temperatur (°C)",
    "vibration_mm_s": "Vibration (mm/s)",
    "pressure_bar":   "Druck (bar)",
    "cycle_time_s":   "Zykluszeit (s)",
}


def _save(fig: plt.Figure, name: str) -> Path:
    """Speichert eine Matplotlib-Figure als PNG.

    Parameters
    ----------
    fig : plt.Figure
        Zu speichernde Figure.
    name : str
        Dateiname ohne Erweiterung.

    Returns
    -------
    Path
        Pfad zur gespeicherten Datei.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Plot gespeichert: %s", path)
    return path


# ---------------------------------------------------------------------------
# Plot 1 – Zeitreihe
# ---------------------------------------------------------------------------

def plot_timeseries(
    df: pd.DataFrame,
    sensor: str = "temperature_c",
    machine: str = "MED-INJ-01",
) -> Path:
    """Zeitreihenverlauf eines Sensors mit markierten Anomalien.

    Anomalien (``anomaly_combined == True``) werden als rote Punkte
    dargestellt, Normalwerte als grüne Linie — so ist die Abweichung
    auf einen Blick erkennbar.

    Parameters
    ----------
    df : pd.DataFrame
        Datensatz mit Anomalie-Flags.
    sensor : str
        Zu plottender Sensor (Default: ``temperature_c``).
    machine : str
        Maschinenfilter (Default: ``MED-INJ-01``).

    Returns
    -------
    Path
        Pfad zum gespeicherten Plot.
    """
    data = df[df["machine_id"] == machine].copy()
    data.sort_values("timestamp", inplace=True)

    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)

    # Normalwerte
    ax.plot(
        data["timestamp"],
        data[sensor],
        color=NORMAL_COLOR,
        linewidth=0.8,
        alpha=0.85,
        label="Normal",
    )

    # Anomalien als Scatter
    anom = data[data["anomaly_combined"]]
    ax.scatter(
        anom["timestamp"],
        anom[sensor],
        color=ANOMALY_COLOR,
        zorder=5,
        s=20,
        label=f"Anomalie (n={len(anom)})",
    )

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
    fig.autofmt_xdate()
    ax.set_title(f"Zeitreihe – {SENSOR_LABELS[sensor]} | {machine}")
    ax.set_xlabel("Zeit")
    ax.set_ylabel(SENSOR_LABELS[sensor])
    ax.legend()

    return _save(fig, f"01_timeseries_{sensor}_{machine}")


# ---------------------------------------------------------------------------
# Plot 2 – Z-Score-Heatmap
# ---------------------------------------------------------------------------

def plot_zscore_heatmap(df: pd.DataFrame) -> Path:
    """Heatmap der mittleren Z-Scores pro Maschine und Sensor.

    Ein hoher |Z-Score| zeigt an, dass eine Maschine dauerhaft außerhalb
    des Normalbereichs läuft — ein frühes Warnsignal für Verschleiß.
    Die Heatmap erlaubt den direkten Maschinenvergleich ohne Zeitreihen
    einzeln betrachten zu müssen.

    Parameters
    ----------
    df : pd.DataFrame
        Datensatz mit Z-Score-Spalten (``<sensor>_zscore``).

    Returns
    -------
    Path
        Pfad zum gespeicherten Plot.
    """
    zscore_cols = [f"{s}_zscore" for s in SENSOR_LABELS]
    pivot = df.groupby("machine_id")[zscore_cols].mean().abs()
    pivot.columns = [SENSOR_LABELS[c.replace("_zscore", "")] for c in pivot.columns]

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".2f",
        cmap="YlOrRd",
        linewidths=0.5,
        ax=ax,
        cbar_kws={"label": "Ø |Z-Score|"},
    )
    ax.set_title("Mittlerer |Z-Score| pro Maschine und Sensor")
    ax.set_ylabel("Maschine")

    return _save(fig, "02_zscore_heatmap")


# ---------------------------------------------------------------------------
# Plot 3 – IQR-Boxplots
# ---------------------------------------------------------------------------

def plot_iqr_boxplots(df: pd.DataFrame) -> Path:
    """Boxplots aller Sensoren, aufgeteilt nach Normal / Anomalie.

    Der Boxplot zeigt Median, IQR und Ausreißer.  Die Gegenüberstellung
    Normal/Anomalie macht deutlich, in welchem Wertebereich die Anomalie-
    Erkennung anschlägt und ob die IQR-Grenzen angemessen gesetzt sind.

    Parameters
    ----------
    df : pd.DataFrame
        Datensatz mit ``anomaly_combined``-Spalte.

    Returns
    -------
    Path
        Pfad zum gespeicherten Plot.
    """
    fig, axes = plt.subplots(1, len(SENSOR_LABELS), figsize=(16, 5))

    for ax, (sensor, label) in zip(axes, SENSOR_LABELS.items()):
        plot_df = df[["anomaly_combined", sensor]].copy()
        plot_df["Status"] = plot_df["anomaly_combined"].map(
            {True: "Anomalie", False: "Normal"}
        )
        sns.boxplot(
            data=plot_df,
            x="Status",
            y=sensor,
            hue="Status",
            palette={"Normal": NORMAL_COLOR, "Anomalie": ANOMALY_COLOR},
            legend=False,
            ax=ax,
            flierprops={"marker": ".", "markersize": 3},
        )
        ax.set_title(label)
        ax.set_xlabel("")
        ax.set_ylabel(label)

    fig.suptitle("Sensorverteilung: Normal vs. Anomalie (IQR-Methode)", y=1.02)
    fig.tight_layout()

    return _save(fig, "03_iqr_boxplots")


# ---------------------------------------------------------------------------
# Plot 4 – Kumulative Anomaliezählung
# ---------------------------------------------------------------------------

def plot_anomaly_timeline(df: pd.DataFrame) -> Path:
    """Kumulierte Anomaliezählung über die Zeit pro Maschine.

    Ein überproportionaler Anstieg der Kurvensteigung kann auf
    beschleunigten Verschleiß hinweisen — das klassische Signal für
    einen bevorstehenden Ausfall.

    Parameters
    ----------
    df : pd.DataFrame
        Datensatz mit ``anomaly_combined``-Spalte.

    Returns
    -------
    Path
        Pfad zum gespeicherten Plot.
    """
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)

    for machine, grp in df.groupby("machine_id"):
        grp = grp.sort_values("timestamp")
        cumsum = grp["anomaly_combined"].cumsum()
        ax.plot(grp["timestamp"], cumsum, label=machine, linewidth=1.5)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    fig.autofmt_xdate()
    ax.set_title("Kumulierte Anomalien pro Maschine")
    ax.set_xlabel("Zeit")
    ax.set_ylabel("Anzahl Anomalien (kumuliert)")
    ax.legend(title="Maschine")

    return _save(fig, "04_anomaly_timeline")


# ---------------------------------------------------------------------------
# Plot 5 – Korrelationsmatrix
# ---------------------------------------------------------------------------

def plot_correlation_matrix(df: pd.DataFrame) -> Path:
    """Pearson-Korrelationsmatrix der Sensorsignale.

    Hohe Korrelationen zwischen Sensoren (z. B. Temperatur ↔ Vibration)
    können auf systemische Zusammenhänge oder gemeinsame Ursachen von
    Anomalien hinweisen.

    Parameters
    ----------
    df : pd.DataFrame
        Datensatz.

    Returns
    -------
    Path
        Pfad zum gespeicherten Plot.
    """
    corr_df = df[list(SENSOR_LABELS.keys())].rename(columns=SENSOR_LABELS)
    corr = corr_df.corr()

    mask = np.triu(np.ones_like(corr, dtype=bool))
    fig, ax = plt.subplots(figsize=FIGSIZE_SQUARE)
    sns.heatmap(
        corr,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title("Korrelationsmatrix der Sensorsignale")

    return _save(fig, "05_correlation_matrix")


# ---------------------------------------------------------------------------
# Alle Plots auf einmal
# ---------------------------------------------------------------------------

def generate_all_plots(df: pd.DataFrame) -> list[Path]:
    """Erzeugt alle Visualisierungen und gibt die Pfade zurück.

    Parameters
    ----------
    df : pd.DataFrame
        Vollständiger, anomalie-gelabelter Datensatz.

    Returns
    -------
    list[Path]
        Liste aller erzeugten Plot-Dateien.
    """
    paths = [
        plot_timeseries(df),
        plot_zscore_heatmap(df),
        plot_iqr_boxplots(df),
        plot_anomaly_timeline(df),
        plot_correlation_matrix(df),
    ]
    logger.info("%d Plots erzeugt.", len(paths))
    return paths


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    from pipeline import run_pipeline  # noqa: PLC0415
    from anomaly_detection import run_anomaly_detection  # noqa: PLC0415

    df_proc = run_pipeline()
    df_scored = run_anomaly_detection(df_proc)
    generate_all_plots(df_scored)
