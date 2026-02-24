# Portfolio - Software & Daten Projekte

> Drei eigenständige Projekte die unterschiedliche Kernkompetenzen der IT-Ausbildung demonstrieren.  
> Jedes Projekt ist vollständig lauffähig, dokumentiert und getestet.

---

## Quickstart — läuft auf Linux, Windows & macOS

**Voraussetzung:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installiert — kein Python, keine venv nötig.

```bash
# Repository klonen
git clone https://github.com/ContinuumHQ/portfolio.git
cd portfolio

# Alle drei Projekte auf einmal starten
docker-compose up

# Einzeln starten
docker-compose up predictive-maintenance
docker-compose up sales-dashboard
docker-compose up network-monitor
```

Outputs (Plots, Reports, Logs) landen automatisch in den jeweiligen `docs/` Unterordnern.

---

## Übersicht

| Projekt | Schwerpunkt | Ausbildungsprofil | Stack |
|---|---|---|---|
| [Predictive Maintenance](#1-predictive-maintenance) | Softwareentwicklung, Datenanalyse | **FIAE** | Python, Pandas, Matplotlib |
| [Network Monitor](#2-network-monitor) | Systemintegration, Deployment | **FISI** | Python, Docker, Bash, systemd |
| [Sales Dashboard](#3-sales-dashboard) | Datenbankdesign, Reporting | **FIDP** | Python, SQLite, MongoDB, Excel |

Alle drei Projekte entstammen eigenem Antrieb und wurden ohne Kursvorlage entwickelt. Sie zeigen Verständnis für Softwarearchitektur, sauberen Code (PEP 8), Testbarkeit und praxisnahe Dokumentation.

---

## 1. Predictive Maintenance

**-> [`predictive_maintenance/`](./predictive_maintenance/)**

Eine vollständige Datenpipeline für vorausschauende Wartung von Produktionsmaschinen in der medizintechnischen Fertigung.

**Was es zeigt:**
- Strukturierter Aufbau einer mehrstufigen Datenpipeline (Generierung -> Bereinigung -> Feature Engineering -> Anomalieerkennung -> Visualisierung)
- Zwei statistische Anomalie-Methoden (Z-Score + IQR) mit begründeter Methodenwahl
- Professionelle Codedokumentation (NumPy-Docstrings, Logging, argparse-CLI)
- 13 Unit-Tests mit pytest-Fixtures

**Schnellstart:**
```bash
cd predictive_maintenance
pip install -r requirements.txt
python main.py
```

---

## 2. Network Monitor

**-> [`network_monitor/`](./network_monitor/)**

Ein automatisiertes Netzwerk-Überwachungstool das Hosts per ICMP-Ping und TCP-Port-Check prüft und strukturierte HTML- und JSON-Reports erstellt.

**Was es zeigt:**
- Netzwerk-Grundverständnis (ICMP, TCP, Ports, Routing)
- Deployment-Kenntnisse: Docker-Container, systemd-Service, Bash-Installationsskript
- YAML-basierte Konfiguration (wie in Ansible/Kubernetes üblich)
- Drei-Zustands-Modell (ONLINE / DEGRADED / OFFLINE) für reale Monitoring-Anforderungen
- 11 Unit-Tests mit unittest.mock für netzwerkfreies Testen

**Schnellstart:**
```bash
cd network_monitor
pip install -r requirements.txt
python main.py --host 192.168.1.1 --ports 22 80 443
```

**Mit Docker:**
```bash
cd network_monitor
docker-compose up -d
```

---

## 3. Sales Dashboard

**-> [`sales_dashboard/`](./sales_dashboard/)**

Eine Business-Intelligence-Pipeline mit relationalem Datenbankdesign, SQL-Aggregationen, vier Analyseplots und automatischem mehrseitigem Excel-Report.

**Was es zeigt:**
- Relationales Datenbankdesign (Star-Schema, Indizes, Fremdschlüssel)
- SQL-Kenntnisse: JOIN, GROUP BY, Aggregatfunktionen, Subqueries
- MongoDB-Integration als Ergänzung für dokumentenbasierte Daten (graceful fallback)
- Professionelle Datenvisualisierung und Export-Automatisierung
- 12 Unit-Tests inkl. Reproduzierbarkeitstest

**Schnellstart:**
```bash
cd sales_dashboard
pip install -r requirements.txt
python main.py
```

---

## Gemeinsame Qualitätsmerkmale

Alle drei Projekte folgen denselben Standards:

- **PEP 8** - konsistenter Python-Stil durchgehend
- **Docstrings** - NumPy-Format mit Parameters/Returns-Dokumentation
- **Logging** - strukturiertes `logging`-Modul statt `print()`
- **Reproduzierbarkeit** - fixer Seed, keine Abhängigkeit von Systemzeit
- **CLI** - `argparse` mit sinnvollen Defaults
- **Tests** - lauffähig mit und ohne `pytest`
- **Keine Hardcoded-Pfade** - alles relativ und konfigurierbar

---

## Zertifikate & Kenntnisse

Dieses Portfolio ergänzt folgende abgeschlossene Zertifizierungen:

| Bereich | Zertifikat / Kurs |
|---|---|
| Datenanalyse | Codecademy - Data Analyst |
| Dateningenieurwesen | Codecademy - Data Engineer |
| Machine Learning | Codecademy - Data Scientist for ML |
| Programmierung | Codecademy - Python 3, C++ Introduction |
| Datenbanken | Codecademy - MongoDB |
| Netzwerk | Cisco CCST - 5/7 Vorbereitungsmodule abgeschlossen |

---

## Autor

Portfolio für Bewerbungen im Bereich Fachinformatik (Ausbildung ab 2025/2026).  
Kontakt auf Anfrage.
