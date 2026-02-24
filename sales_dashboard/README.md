# Sales Dashboard - Datenanalyse & Reporting

> **Portfolio-Projekt** | Daten- & Prozessmanagement  
> Domäne: Business Intelligence, Datenbankdesign, Reporting  
> Stack: Python · SQLite · MongoDB · Pandas · Matplotlib · Seaborn · Excel

---

## Projektziel

Dieses Projekt demonstriert eine vollständige BI-Pipeline: Rohdaten werden in einer relationalen Datenbank strukturiert gespeichert, über SQL aggregiert, visuell aufbereitet und als professioneller Excel-Report exportiert. Ergänzend zeigt das Projekt den Einsatz von MongoDB als dokumentenbasierte Ergänzung für unstrukturierte Daten.

---

## Projektstruktur

```
sales_dashboard/
├── database.py         # SQLite-Schema, Abfragen, MongoDB-Anbindung
├── data_seeder.py      # Synthetischer Datengenerator (2.000 Verkäufe)
├── visualizations.py   # 4 Analyseplots (Matplotlib + Seaborn)
├── exporter.py         # CSV- und Excel-Export (mehrseitig)
├── main.py             # CLI-Einstiegspunkt
├── requirements.txt
├── tests/
│   └── test_dashboard.py  # 12 Unit-Tests
├── data/
│   └── sales.db        # SQLite-Datenbank (wird automatisch erstellt)
└── docs/               # Generierte Plots und Reports
```

---

## Quickstart

```bash
# 1. Abhängigkeiten installieren
pip install -r requirements.txt

# 2. Vollständiger Durchlauf (DB + Plots + Reports)
python main.py

# 3. Nur Exports (ohne neue Plots)
python main.py --no-plots

# 4. Mehr Testdaten generieren
python main.py --records 10000
```

---

## Datenbankdesign

Das relationale Schema folgt dem Star-Schema-Prinzip mit einer zentralen Faktentabelle und zwei Dimensionstabellen:

```
products (id, name, category, unit_price)
    │
    │  1:N
    ▼
sales (id, sale_date, product_id, customer_id, quantity, discount, revenue)
    ▲
    │  1:N
    │
customers (id, name, region, segment)
```

Indizes auf `sale_date`, `product_id` und `customer_id` optimieren die Abfrageperformance bei großen Datenmengen.

**MongoDB-Integration (optional):** Die Klasse `get_mongo_collection()` in `database.py` zeigt, wie ein Hybrid-Ansatz aussieht — relationale Strukturdaten in SQLite, Event-Logs oder unstrukturierte Daten in MongoDB. Bei nicht verfügbarer MongoDB-Instanz fällt das System graceful zurück auf SQLite-only.

---

## Synthetische Daten

Der Generator (`data_seeder.py`) erstellt realistische Verkaufsdaten mit:

- **Saisonalität:** Q4 (Okt-Dez) mit 40% Umsatzsteigerung
- **Produktkategorien:** Software, Hardware, Service, Lizenz
- **Kundensegmente:** B2B und B2C nach Regionen (Nord/Süd/West/Ost)
- **Rabattstruktur:** Zufällige Rabatte 0-20% mit realistischer Gewichtung
- **Reproduzierbarkeit:** Fixer Seed -> identische Daten bei jedem Run

---

## Visualisierungen

| Datei                        | Inhalt                                        |
|------------------------------|-----------------------------------------------|
| `01_monthly_revenue.png`     | Monatsumsatz nach Kategorie (gestapelt)       |
| `02_top_products.png`        | Top 10 Produkte nach Gesamtumsatz             |
| `03_regional_heatmap.png`    | Umsatz-Heatmap: Region × Kundensegment        |
| `04_discount_vs_revenue.png` | Streudiagramm: Rabatt vs. Umsatz pro Verkauf  |

---

## Reports

Jeder Lauf erzeugt automatisch zwei Exportdateien in `docs/`:

**CSV** (`sales_summary_*.csv`) — UTF-8 mit BOM, Semikolon-separiert, direkt in Excel importierbar.

**Excel** (`sales_report_*.xlsx`) — Mehrseitig mit automatisch angepassten Spaltenbreiten:
- Sheet 1: Monatliche Umsatzzusammenfassung
- Sheet 2: Top-Produkte-Ranking
- Sheet 3: Regionale Performance
- Sheet 4: Vollständige Rohdaten

---

## Tests

```bash
python tests/test_dashboard.py    # Manuell
pytest tests/test_dashboard.py -v # Mit pytest
```

12 Tests decken ab: Schemavalidierung, Datengenerierung, Wertebereiche, Datumsformate, Reproduzierbarkeit, alle drei SQL-Abfragen.

---

## Technische Entscheidungen

**Warum SQLite statt PostgreSQL?** SQLite ermöglicht Zero-Config-Deployment — keine Datenbank-Installation nötig. Für ein Produktivsystem mit mehreren gleichzeitigen Schreibzugriffen würde die Migration zu PostgreSQL ca. 2 Stunden erfordern, da die gleichen SQLAlchemy-kompatiblen Queries verwendet werden könnten.

**Warum openpyxl für Excel?** Im Gegensatz zu `xlwt` unterstützt openpyxl das aktuelle `.xlsx`-Format und ermöglicht programmatische Formatierung (Spaltenbreiten, Tabellenblätter) ohne Excel-Installation.

**Warum Seaborn + Matplotlib?** Seaborn liefert statistisch orientierte Plot-Typen (Heatmaps, erweiterte Box-Plots) mit konsistenter Ästhetik. Matplotlib als Backend ermöglicht pixelgenaue Anpassung für Print-qualitative Reports.

---

## Mögliche Erweiterungen

- Interaktives Web-Dashboard (Plotly Dash oder Streamlit)
- Automatisierter E-Mail-Versand der Excel-Reports (smtplib)
- Live-Datenbankanbindung (PostgreSQL + SQLAlchemy)
- Forecast-Modul (Prophet oder ARIMA für Umsatzprognosen)
- REST-API für externe Datenzulieferung (FastAPI)

---

## Autor

Portfolio-Projekt zur Demonstration von Fähigkeiten in Datenbankdesign, Datenanalyse und automatisiertem Reporting.  
Kontakt auf Anfrage.
