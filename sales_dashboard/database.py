"""
Datenbankschicht für Sales Dashboard.
Unterstützt SQLite (Standard) und MongoDB (optional, via pymongo).
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime, date
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_PATH = Path("data/sales.db")
DB_PATH.parent.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# SQLite – relationale Hauptdatenbank
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,
    unit_price  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    region      TEXT NOT NULL,
    segment     TEXT NOT NULL    -- B2B / B2C
);

CREATE TABLE IF NOT EXISTS sales (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_date    TEXT NOT NULL,
    product_id   INTEGER REFERENCES products(id),
    customer_id  INTEGER REFERENCES customers(id),
    quantity     INTEGER NOT NULL,
    discount     REAL    DEFAULT 0.0,
    revenue      REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sales_date     ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_product  ON sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);
"""


@contextmanager
def get_connection(db_path: Path = DB_PATH):
    """Kontextmanager für SQLite-Verbindungen mit automatischem Commit/Rollback."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path = DB_PATH) -> None:
    """Erstellt das Datenbankschema falls noch nicht vorhanden."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
    logger.info("Datenbank initialisiert: %s", db_path)


def insert_sales_batch(records: list[dict], db_path: Path = DB_PATH) -> int:
    """
    Fügt mehrere Verkaufsdatensätze in einem Batch ein.

    Parameters
    ----------
    records : list[dict]
        Jedes Dict muss sale_date, product_id, customer_id,
        quantity, discount, revenue enthalten.
    db_path : Path
        Pfad zur SQLite-Datenbank.

    Returns
    -------
    int
        Anzahl eingefügter Datensätze.
    """
    sql = """
    INSERT INTO sales (sale_date, product_id, customer_id, quantity, discount, revenue)
    VALUES (:sale_date, :product_id, :customer_id, :quantity, :discount, :revenue)
    """
    with get_connection(db_path) as conn:
        conn.executemany(sql, records)
    logger.info("%d Verkaufsdatensätze eingefügt.", len(records))
    return len(records)


def query_sales_summary(db_path: Path = DB_PATH) -> list[dict]:
    """
    Aggregierte Umsatzübersicht: Monat, Kategorie, Umsatz, Verkäufe.

    Returns
    -------
    list[dict]
        Aggregierte Zeilen sortiert nach Monat.
    """
    sql = """
    SELECT
        strftime('%Y-%m', s.sale_date)  AS month,
        p.category,
        SUM(s.revenue)                  AS total_revenue,
        COUNT(s.id)                     AS total_sales,
        AVG(s.discount)                 AS avg_discount
    FROM sales s
    JOIN products p ON s.product_id = p.id
    GROUP BY month, p.category
    ORDER BY month
    """
    with get_connection(db_path) as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


def query_top_products(limit: int = 10, db_path: Path = DB_PATH) -> list[dict]:
    """Top-Produkte nach Umsatz."""
    sql = """
    SELECT p.name, p.category, SUM(s.revenue) AS total_revenue, SUM(s.quantity) AS units_sold
    FROM sales s JOIN products p ON s.product_id = p.id
    GROUP BY p.id ORDER BY total_revenue DESC LIMIT ?
    """
    with get_connection(db_path) as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]


def query_regional_performance(db_path: Path = DB_PATH) -> list[dict]:
    """Umsatz nach Region und Kundensegment."""
    sql = """
    SELECT c.region, c.segment, SUM(s.revenue) AS total_revenue, COUNT(DISTINCT c.id) AS customers
    FROM sales s JOIN customers c ON s.customer_id = c.id
    GROUP BY c.region, c.segment ORDER BY total_revenue DESC
    """
    with get_connection(db_path) as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# MongoDB – dokumentenbasierte Ergänzung (optional)
# ---------------------------------------------------------------------------

def get_mongo_collection(uri: str = "mongodb://localhost:27017", db: str = "sales_dashboard"):
    """
    Gibt eine MongoDB-Collection für erweiterte Analysen zurück.
    Benötigt: pip install pymongo

    Verwendung z.B. für unstrukturierte Kundendaten oder Event-Logs,
    die sich nicht gut in ein relationales Schema fügen.
    """
    try:
        from pymongo import MongoClient
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.server_info()  # Verbindungstest
        logger.info("MongoDB verbunden: %s", uri)
        return client[db]["events"]
    except ImportError:
        logger.warning("pymongo nicht installiert – MongoDB-Features deaktiviert.")
        return None
    except Exception as e:
        logger.warning("MongoDB nicht erreichbar (%s) – nur SQLite aktiv.", e)
        return None
