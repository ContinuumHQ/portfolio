"""
Unit-Tests für Sales Dashboard.
Ausführen: pytest tests/test_dashboard.py -v
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db, get_connection, query_sales_summary, query_top_products, query_regional_performance
from data_seeder import seed_master_data, generate_sales


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_db(tmp_path):
    """Temporäre SQLite-Datenbank für jeden Test."""
    db_path = tmp_path / "test_sales.db"
    init_db(db_path)
    seed_master_data(db_path)
    generate_sales(n=200, seed=99, db_path=db_path)
    return db_path


# ---------------------------------------------------------------------------
# Datenbankschema
# ---------------------------------------------------------------------------

def test_schema_tables_exist(temp_db):
    """Alle drei Tabellen müssen existieren."""
    with get_connection(temp_db) as conn:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    assert {"products", "customers", "sales"}.issubset(tables)


def test_products_seeded(temp_db):
    """Stammdaten: mind. 10 Produkte vorhanden."""
    with get_connection(temp_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert count >= 10


def test_customers_seeded(temp_db):
    """Stammdaten: mind. 10 Kunden vorhanden."""
    with get_connection(temp_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    assert count >= 10


# ---------------------------------------------------------------------------
# Datengenerator
# ---------------------------------------------------------------------------

def test_sales_count(temp_db):
    """200 Verkäufe generiert."""
    with get_connection(temp_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    assert count == 200


def test_revenue_positive(temp_db):
    """Alle Umsatzwerte müssen positiv sein."""
    with get_connection(temp_db) as conn:
        min_rev = conn.execute("SELECT MIN(revenue) FROM sales").fetchone()[0]
    assert min_rev > 0


def test_discount_range(temp_db):
    """Rabatte müssen zwischen 0 und 1 liegen."""
    with get_connection(temp_db) as conn:
        row = conn.execute("SELECT MIN(discount), MAX(discount) FROM sales").fetchone()
    assert row[0] >= 0.0
    assert row[1] <= 1.0


def test_dates_valid(temp_db):
    """Alle Datumsangaben müssen gültiges ISO-Format haben."""
    with get_connection(temp_db) as conn:
        dates = [r[0] for r in conn.execute("SELECT DISTINCT sale_date FROM sales").fetchall()]
    for d in dates:
        datetime.strptime(d, "%Y-%m-%d")  # Wirft ValueError bei ungültigem Format


def test_reproducibility(temp_db):
    """Gleicher Seed → gleiche Gesamt-Revenue."""
    with get_connection(temp_db) as conn:
        rev1 = conn.execute("SELECT SUM(revenue) FROM sales").fetchone()[0]

    import tempfile
    from pathlib import Path as P
    db2 = P(tempfile.mktemp(suffix=".db"))
    init_db(db2)
    seed_master_data(db2)
    generate_sales(n=200, seed=99, db_path=db2)
    with get_connection(db2) as conn:
        rev2 = conn.execute("SELECT SUM(revenue) FROM sales").fetchone()[0]

    assert abs(rev1 - rev2) < 0.01


# ---------------------------------------------------------------------------
# Abfragen
# ---------------------------------------------------------------------------

def test_sales_summary_not_empty(temp_db):
    """Monatliche Zusammenfassung muss Daten enthalten."""
    result = query_sales_summary(temp_db)
    assert len(result) > 0


def test_sales_summary_fields(temp_db):
    """Jede Zeile der Zusammenfassung hat alle erwarteten Felder."""
    result = query_sales_summary(temp_db)
    required = {"month", "category", "total_revenue", "total_sales", "avg_discount"}
    for row in result:
        assert required.issubset(row.keys())


def test_top_products_limit(temp_db):
    """Top-Produkte-Abfrage respektiert das Limit."""
    result = query_top_products(limit=5, db_path=temp_db)
    assert len(result) <= 5


def test_regional_performance_fields(temp_db):
    """Regionale Performance enthält Region und Segment."""
    result = query_regional_performance(temp_db)
    assert len(result) > 0
    for row in result:
        assert "region" in row
        assert "segment" in row
        assert row["total_revenue"] > 0


# ---------------------------------------------------------------------------
# Manueller Test-Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile, os
    db = Path(tempfile.mktemp(suffix=".db"))
    init_db(db)
    seed_master_data(db)
    generate_sales(n=200, seed=99, db_path=db)

    tests = [
        lambda: test_schema_tables_exist(db),
        lambda: test_products_seeded(db),
        lambda: test_customers_seeded(db),
        lambda: test_sales_count(db),
        lambda: test_revenue_positive(db),
        lambda: test_discount_range(db),
        lambda: test_dates_valid(db),
        lambda: test_reproducibility(db),
        lambda: test_sales_summary_not_empty(db),
        lambda: test_sales_summary_fields(db),
        lambda: test_top_products_limit(db),
        lambda: test_regional_performance_fields(db),
    ]
    names = [
        "schema_tables_exist", "products_seeded", "customers_seeded",
        "sales_count", "revenue_positive", "discount_range", "dates_valid",
        "reproducibility", "sales_summary_not_empty", "sales_summary_fields",
        "top_products_limit", "regional_performance_fields",
    ]
    passed = 0
    for t, name in zip(tests, names):
        try:
            t()
            print(f"  ✓ {name}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
    print(f"\n{passed}/{len(tests)} Tests bestanden.")
    os.unlink(db)
