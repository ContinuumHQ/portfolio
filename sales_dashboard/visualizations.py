"""
Visualisierungsmodul für Sales Dashboard.
Erstellt 4 Analyseplots als PNG-Dateien.
"""

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd

from database import query_sales_summary, query_top_products, query_regional_performance, DB_PATH

logger = logging.getLogger(__name__)
sns.set_theme(style="darkgrid")

PLOT_DIR = Path("docs")
PLOT_DIR.mkdir(exist_ok=True)

COLORS = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c"]


def plot_monthly_revenue(db_path=DB_PATH) -> Path:
    """Monatlicher Umsatz nach Kategorie als gestapeltes Balkendiagramm."""
    data = query_sales_summary(db_path)
    df = pd.DataFrame(data)
    pivot = df.pivot_table(index="month", columns="category", values="total_revenue", aggfunc="sum").fillna(0)

    fig, ax = plt.subplots(figsize=(12, 5))
    pivot.plot(kind="bar", stacked=True, ax=ax, color=COLORS[:len(pivot.columns)], width=0.75)

    ax.set_title("Monatlicher Umsatz nach Kategorie", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Monat")
    ax.set_ylabel("Umsatz (€)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f} €"))
    ax.set_xticklabels(pivot.index, rotation=45, ha="right")
    ax.legend(title="Kategorie", bbox_to_anchor=(1.01, 1), loc="upper left")
    plt.tight_layout()

    path = PLOT_DIR / "01_monthly_revenue.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logger.info("Plot gespeichert: %s", path)
    return path


def plot_top_products(db_path=DB_PATH) -> Path:
    """Top-10-Produkte nach Umsatz als horizontales Balkendiagramm."""
    data = query_top_products(limit=10, db_path=db_path)
    df = pd.DataFrame(data).sort_values("total_revenue")

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(df["name"], df["total_revenue"], color=COLORS[0], alpha=0.85)

    for bar in bars:
        ax.text(
            bar.get_width() + max(df["total_revenue"]) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f'{bar.get_width():,.0f} €',
            va="center", fontsize=8
        )

    ax.set_title("Top 10 Produkte nach Umsatz", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Gesamtumsatz (€)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f} €"))
    plt.tight_layout()

    path = PLOT_DIR / "02_top_products.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logger.info("Plot gespeichert: %s", path)
    return path


def plot_regional_heatmap(db_path=DB_PATH) -> Path:
    """Umsatz-Heatmap: Region × Kundensegment."""
    data = query_regional_performance(db_path)
    df = pd.DataFrame(data)
    pivot = df.pivot_table(index="region", columns="segment", values="total_revenue", aggfunc="sum").fillna(0)

    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(
        pivot, annot=True, fmt=",.0f", cmap="Blues",
        linewidths=0.5, ax=ax,
        annot_kws={"size": 10}
    )
    ax.set_title("Umsatz nach Region & Kundensegment (€)", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Region")
    ax.set_xlabel("Segment")
    plt.tight_layout()

    path = PLOT_DIR / "03_regional_heatmap.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logger.info("Plot gespeichert: %s", path)
    return path


def plot_discount_vs_revenue(db_path=DB_PATH) -> Path:
    """Streudiagramm: Rabatt vs. Umsatz pro Verkauf."""
    from database import get_connection
    sql = """
    SELECT s.discount, s.revenue, p.category
    FROM sales s JOIN products p ON s.product_id = p.id
    """
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(sql, conn)

    fig, ax = plt.subplots(figsize=(9, 5))
    categories = df["category"].unique()
    for i, cat in enumerate(categories):
        sub = df[df["category"] == cat]
        ax.scatter(sub["discount"] * 100, sub["revenue"],
                   alpha=0.4, s=20, label=cat, color=COLORS[i % len(COLORS)])

    ax.set_title("Rabatt vs. Umsatz pro Verkauf", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Rabatt (%)")
    ax.set_ylabel("Umsatz (€)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f} €"))
    ax.legend(title="Kategorie", bbox_to_anchor=(1.01, 1), loc="upper left")
    plt.tight_layout()

    path = PLOT_DIR / "04_discount_vs_revenue.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logger.info("Plot gespeichert: %s", path)
    return path


def generate_all_plots(db_path=DB_PATH) -> list[Path]:
    """Erstellt alle vier Analyse-Plots."""
    paths = [
        plot_monthly_revenue(db_path),
        plot_top_products(db_path),
        plot_regional_heatmap(db_path),
        plot_discount_vs_revenue(db_path),
    ]
    logger.info("Alle %d Plots erstellt.", len(paths))
    return paths
