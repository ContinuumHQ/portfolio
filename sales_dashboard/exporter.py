"""
Report-Export für Sales Dashboard.
Exportiert aggregierte Auswertungen als CSV und Excel.
"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from database import (
    query_sales_summary,
    query_top_products,
    query_regional_performance,
    get_connection,
    DB_PATH,
)

logger = logging.getLogger(__name__)
EXPORT_DIR = Path("docs")
EXPORT_DIR.mkdir(exist_ok=True)


def export_csv(db_path: Path = DB_PATH) -> Path:
    """Exportiert alle Kerndaten als CSV-Datei."""
    summary = pd.DataFrame(query_sales_summary(db_path))
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"sales_summary_{ts}.csv"
    summary.to_csv(path, index=False, sep=";", encoding="utf-8-sig")
    logger.info("CSV-Export: %s", path)
    return path


def export_excel(db_path: Path = DB_PATH) -> Path:
    """
    Exportiert einen mehrseitigen Excel-Report.
    Enthält: Monatsumsatz, Top-Produkte, Regionale Performance, Rohdaten.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"sales_report_{ts}.xlsx"

    summary_df = pd.DataFrame(query_sales_summary(db_path))
    products_df = pd.DataFrame(query_top_products(limit=10, db_path=db_path))
    regional_df = pd.DataFrame(query_regional_performance(db_path))

    sql_raw = """
    SELECT s.sale_date, p.name AS product, p.category, c.name AS customer,
           c.region, c.segment, s.quantity, s.discount, s.revenue
    FROM sales s
    JOIN products p ON s.product_id = p.id
    JOIN customers c ON s.customer_id = c.id
    ORDER BY s.sale_date
    """
    with get_connection(db_path) as conn:
        raw_df = pd.read_sql_query(sql_raw, conn)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Monatsumsatz", index=False)
        products_df.to_excel(writer, sheet_name="Top Produkte", index=False)
        regional_df.to_excel(writer, sheet_name="Regionale Performance", index=False)
        raw_df.to_excel(writer, sheet_name="Rohdaten", index=False)

        # Spaltenbreiten automatisch anpassen
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col) + 3
                ws.column_dimensions[col[0].column_letter].width = min(max_len, 40)

    logger.info("Excel-Report: %s", path)
    return path
