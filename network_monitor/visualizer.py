"""
Visualisierungsmodul fuer Network Monitor.
Erstellt 3 Plots aus den JSON-Logs: Status-Uebersicht, Latenz-Verlauf, Port-Heatmap.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd

logger = logging.getLogger(__name__)
sns.set_theme(style="darkgrid")

PLOT_DIR = Path("docs")
PLOT_DIR.mkdir(exist_ok=True)

STATUS_COLORS = {"ONLINE": "#2ecc71", "DEGRADED": "#f39c12", "OFFLINE": "#e74c3c"}


def load_latest_reports(report_dir: Path = PLOT_DIR, max_reports: int = 20) -> list[dict]:
    """
    Laedt die neuesten JSON-Reports aus dem docs-Verzeichnis.

    Parameters
    ----------
    report_dir : Path
        Verzeichnis mit den JSON-Reports.
    max_reports : int
        Maximale Anzahl zu ladender Reports.

    Returns
    -------
    list[dict]
        Liste der geladenen Report-Dicts, chronologisch sortiert.
    """
    files = sorted(report_dir.glob("report_*.json"))[-max_reports:]
    reports = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            reports.append(json.load(fh))
    return reports


def plot_status_overview(reports: list[dict]) -> Path:
    """
    Balkendiagramm: Anteil ONLINE / DEGRADED / OFFLINE ueber alle Scans.
    """
    rows = []
    for r in reports:
        ts = datetime.fromisoformat(r["generated_at"]).strftime("%H:%M")
        rows.append({
            "Zeit": ts,
            "ONLINE": r["online"],
            "DEGRADED": r["degraded"],
            "OFFLINE": r["offline"],
        })

    df = pd.DataFrame(rows).set_index("Zeit")

    fig, ax = plt.subplots(figsize=(12, 4))
    df.plot(
        kind="bar", stacked=True, ax=ax,
        color=[STATUS_COLORS["ONLINE"], STATUS_COLORS["DEGRADED"], STATUS_COLORS["OFFLINE"]],
        width=0.75
    )
    ax.set_title("Netzwerkstatus pro Scan", fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Scan-Zeitpunkt")
    ax.set_ylabel("Anzahl Geraete")
    ax.set_xticklabels(df.index, rotation=45, ha="right")
    ax.legend(loc="upper right")
    plt.tight_layout()

    path = PLOT_DIR / "01_status_overview.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logger.info("Plot gespeichert: %s", path)
    return path


def plot_latency_history(reports: list[dict]) -> Path:
    """
    Liniendiagramm: Latenzentwicklung je Host ueber die Zeit.
    """
    rows = []
    for r in reports:
        ts = datetime.fromisoformat(r["generated_at"])
        for result in r["results"]:
            if result["ping_ok"] and result["ping_latency_ms"] is not None:
                rows.append({
                    "Zeit": ts,
                    "Host": result["host"],
                    "Latenz_ms": result["ping_latency_ms"],
                })

    if not rows:
        logger.warning("Keine Latenzdaten vorhanden - ueberspringe Latenz-Plot")
        return None

    df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(12, 5))
    for host in df["Host"].unique():
        sub = df[df["Host"] == host]
        ax.plot(sub["Zeit"], sub["Latenz_ms"], marker="o", markersize=4, label=host, linewidth=1.5)

    ax.set_title("Latenzentwicklung je Host (ms)", fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Zeit")
    ax.set_ylabel("Latenz (ms)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f} ms"))
    ax.legend(title="Host", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    plt.tight_layout()

    path = PLOT_DIR / "02_latency_history.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logger.info("Plot gespeichert: %s", path)
    return path


def plot_port_heatmap(reports: list[dict]) -> Path:
    """
    Heatmap: Verfuegbarkeit je Host und Port ueber alle Scans.
    Wert 1 = offen, 0 = geschlossen, NaN = nicht geprueft.
    """
    if not reports:
        return None

    latest = reports[-1]
    rows = []
    for result in latest["results"]:
        host = result["host"]
        for port in result["open_ports"]:
            rows.append({"Host": host, "Port": str(port), "Status": 1})
        for port in result["closed_ports"]:
            rows.append({"Host": host, "Port": str(port), "Status": 0})

    if not rows:
        logger.warning("Keine Port-Daten vorhanden - ueberspringe Port-Heatmap")
        return None

    df = pd.DataFrame(rows)
    pivot = df.pivot_table(index="Host", columns="Port", values="Status", aggfunc="mean")

    fig, ax = plt.subplots(figsize=(max(6, len(pivot.columns) * 1.2), max(4, len(pivot) * 0.8)))
    sns.heatmap(
        pivot, annot=True, fmt=".0f", cmap="RdYlGn",
        vmin=0, vmax=1, linewidths=0.5, ax=ax,
        cbar_kws={"label": "1=offen  0=geschlossen"}
    )
    ax.set_title("Port-Status je Host (letzter Scan)", fontsize=13, fontweight="bold", pad=10)
    ax.set_ylabel("Host")
    ax.set_xlabel("Port")
    plt.tight_layout()

    path = PLOT_DIR / "03_port_heatmap.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logger.info("Plot gespeichert: %s", path)
    return path


def generate_all_plots(report_dir: Path = PLOT_DIR) -> list[Path]:
    """Laedt alle Reports und erstellt alle drei Plots."""
    reports = load_latest_reports(report_dir)
    if not reports:
        logger.warning("Keine Reports gefunden - zuerst einen Scan ausfuehren: python main.py")
        return []

    paths = []
    for fn in [plot_status_overview, plot_latency_history, plot_port_heatmap]:
        result = fn(reports)
        if result:
            paths.append(result)

    logger.info("%d Plots erstellt.", len(paths))
    return paths
