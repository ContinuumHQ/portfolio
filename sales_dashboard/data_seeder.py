"""
Synthetischer Datengenerator für das Sales Dashboard.
Erstellt realistische Testdaten für Produkte, Kunden und Verkäufe.
"""

import random
import logging
from datetime import datetime, timedelta
from pathlib import Path

from database import get_connection, init_db, DB_PATH

logger = logging.getLogger(__name__)

PRODUCTS = [
    ("Produkt A – Basic",     "Software",  49.00),
    ("Produkt B – Pro",       "Software",  149.00),
    ("Produkt C – Enterprise","Software",  499.00),
    ("Hardware Kit S",        "Hardware",  89.00),
    ("Hardware Kit L",        "Hardware",  229.00),
    ("Support Basic",         "Service",   29.00),
    ("Support Premium",       "Service",   99.00),
    ("Consulting Tag",        "Service",   850.00),
    ("Lizenz Annual",         "Lizenz",    199.00),
    ("Lizenz Multi-User",     "Lizenz",    599.00),
]

CUSTOMERS = [
    ("Alpha GmbH",        "Nord",  "B2B"),
    ("Beta AG",           "Süd",   "B2B"),
    ("Gamma Solutions",   "West",  "B2B"),
    ("Delta Corp",        "Ost",   "B2B"),
    ("Epsilon Tech",      "Nord",  "B2B"),
    ("Kunde Zeta",        "Süd",   "B2C"),
    ("Kunde Eta",         "West",  "B2C"),
    ("Kunde Theta",       "Ost",   "B2C"),
    ("Iota Startup",      "Nord",  "B2B"),
    ("Kappa Handel",      "West",  "B2B"),
]


def seed_master_data(db_path: Path = DB_PATH) -> tuple[list[int], list[int]]:
    """Fügt Stammdaten (Produkte, Kunden) ein falls noch nicht vorhanden."""
    with get_connection(db_path) as conn:
        if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] > 0:
            product_ids = [r[0] for r in conn.execute("SELECT id FROM products").fetchall()]
            customer_ids = [r[0] for r in conn.execute("SELECT id FROM customers").fetchall()]
            return product_ids, customer_ids

        product_ids, customer_ids = [], []
        for name, category, price in PRODUCTS:
            cur = conn.execute(
                "INSERT INTO products (name, category, unit_price) VALUES (?, ?, ?)",
                (name, category, price)
            )
            product_ids.append(cur.lastrowid)

        for name, region, segment in CUSTOMERS:
            cur = conn.execute(
                "INSERT INTO customers (name, region, segment) VALUES (?, ?, ?)",
                (name, region, segment)
            )
            customer_ids.append(cur.lastrowid)

    logger.info("Stammdaten eingefügt: %d Produkte, %d Kunden", len(product_ids), len(customer_ids))
    return product_ids, customer_ids


def generate_sales(
    n: int = 2000,
    seed: int = 42,
    db_path: Path = DB_PATH,
    start_date: datetime | None = None
) -> int:
    """
    Generiert synthetische Verkaufsdaten mit saisonalen Schwankungen.

    Parameters
    ----------
    n : int
        Anzahl der zu generierenden Verkaufsvorgänge.
    seed : int
        Zufallsseed für Reproduzierbarkeit.
    db_path : Path
        Pfad zur Zieldatenbank.
    start_date : datetime, optional
        Startdatum. Standard: 12 Monate vor heute.

    Returns
    -------
    int
        Anzahl eingefügter Datensätze.
    """
    random.seed(seed)
    if start_date is None:
        start_date = datetime(2024, 1, 1)

    product_ids, customer_ids = seed_master_data(db_path)

    with get_connection(db_path) as conn:
        prices = {
            row[0]: row[1]
            for row in conn.execute("SELECT id, unit_price FROM products").fetchall()
        }

    records = []
    for _ in range(n):
        # Saisonalität: Q4 (Okt–Dez) verkauft ~40% mehr
        day_offset = random.randint(0, 364)
        sale_date = start_date + timedelta(days=day_offset)
        seasonal_boost = 1.4 if sale_date.month in (10, 11, 12) else 1.0

        product_id = random.choice(product_ids)
        customer_id = random.choice(customer_ids)
        quantity = random.choices([1, 2, 3, 5, 10], weights=[50, 25, 15, 7, 3])[0]
        discount = random.choices([0.0, 0.05, 0.10, 0.15, 0.20], weights=[40, 25, 20, 10, 5])[0]

        base_revenue = prices[product_id] * quantity * seasonal_boost
        revenue = round(base_revenue * (1 - discount), 2)

        records.append({
            "sale_date": sale_date.strftime("%Y-%m-%d"),
            "product_id": product_id,
            "customer_id": customer_id,
            "quantity": quantity,
            "discount": discount,
            "revenue": revenue,
        })

    with get_connection(db_path) as conn:
        conn.executemany(
            "INSERT INTO sales (sale_date, product_id, customer_id, quantity, discount, revenue) "
            "VALUES (:sale_date, :product_id, :customer_id, :quantity, :discount, :revenue)",
            records
        )

    logger.info("%d Verkaufsdatensätze generiert.", len(records))
    return len(records)


def setup_demo_db(db_path: Path = DB_PATH) -> None:
    """Vollständiges Demo-Setup: Schema + Stammdaten + Verkäufe."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    if count == 0:
        generate_sales(n=2000, seed=42, db_path=db_path)
        logger.info("Demo-Datenbank bereit.")
    else:
        logger.info("Datenbank enthält bereits %d Datensätze – kein Re-Seed.", count)
