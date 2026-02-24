# Network Monitor - Automatisierte Netzwerküberwachung

> **Portfolio-Projekt** | Systemintegration & IT-Infrastruktur  
> Domäne: Netzwerkbetrieb, Monitoring, Deployment  
> Stack: Python · PyYAML · Docker · Bash · systemd

---

## Projektziel

Dieses Tool überwacht automatisiert die Erreichbarkeit und den Port-Status von Netzwerkgeräten in einer lokalen IT-Infrastruktur. Es richtet sich an Szenarien in denen ein IT-Administrator regelmäßig sicherstellen muss, dass Server, Router und Dienste verfügbar sind — und bei Ausfällen sofort strukturierte Reports vorliegen.

---

## Projektstruktur

```
network_monitor/
├── monitor.py           # Ping (ICMP) + Port-Checks (TCP)
├── reporter.py          # JSON- und HTML-Reportgenerierung
├── visualizer.py        # 3 Analyseplots (Status, Latenz, Port-Heatmap)
├── main.py              # CLI-Einstiegspunkt
├── config.yaml          # Geraetekonfiguration (Hosts + Ports)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── scripts/
│   └── setup.sh         # Automatisches Installations-Skript (Arch Linux)
├── tests/
│   └── test_monitor.py  # 11 Unit-Tests
└── docs/                # Generierte Reports (JSON, HTML) und Plots (PNG)
```

---

## Quickstart

```bash
# 1. Abhängigkeiten installieren
pip install -r requirements.txt

# 2. Geräte konfigurieren
nano config.yaml

# 3. Einmaliger Scan
python main.py

# 4. Dauerschleife (Intervall aus config.yaml)
python main.py --loop

# 5. Einzelnen Host prüfen
python main.py --host 192.168.1.1 --ports 22 80 443
```

---

## Deployment

### Als systemd-Service (empfohlen für Produktivbetrieb)

```bash
sudo chmod +x scripts/setup.sh
sudo ./scripts/setup.sh
```

Das Skript installiert alle Abhängigkeiten, erstellt einen systemd-Service und startet ihn dauerhaft. Logs sind über `journalctl -u network-monitor -f` abrufbar.

### Mit Docker

```bash
docker-compose up -d
```

Der Container läuft im `host`-Netzwerkmodus um direkten ICMP-Zugriff zu haben. Reports werden im Volume `./docs` persistent gespeichert.

---

## Konfiguration

`config.yaml` definiert alle zu überwachenden Geräte:

```yaml
scan_interval_seconds: 60

devices:
  - host: "192.168.1.1"
    label: "Router / Gateway"
    ports: [22, 80, 443]

  - host: "192.168.1.10"
    label: "Fileserver"
    ports: [22, 445, 3389]
```

---

## Geräte-Status

| Status     | Bedeutung                                         |
|------------|---------------------------------------------------|
| `ONLINE`   | Ping erfolgreich, alle Ports offen                |
| `DEGRADED` | Ping erfolgreich, aber mind. ein Port geschlossen |
| `OFFLINE`  | Gerät nicht per Ping erreichbar                   |

---

## Reports

Nach jedem Scan werden automatisch zwei Dateien in `docs/` gespeichert:

**JSON-Log** (`report_YYYYMMDD_HHMMSS.json`) - maschinenlesbar, geeignet für Weiterverarbeitung oder Monitoring-Anbindung.

**HTML-Report** (`report_YYYYMMDD_HHMMSS.html`) - visuell aufbereiteter Statusbericht mit farbkodierter Tabelle, direkt im Browser öffenbar.

---

## Visualisierungen

Nach jedem Scan werden automatisch drei Plots in `docs/` erstellt:

| Datei | Inhalt |
|---|---|
| `01_status_overview.png` | Balkendiagramm - Anteil ONLINE/DEGRADED/OFFLINE pro Scan |
| `02_latency_history.png` | Liniendiagramm - Latenzentwicklung je Host ueber die Zeit |
| `03_port_heatmap.png` | Heatmap - Port-Verfuegbarkeit je Host (letzter Scan) |

Die Plots werden aus den JSON-Logs generiert und zeigen Trends ueber mehrere Scans hinweg.

---

## Tests

```bash
python tests/test_monitor.py    # Manuell (kein pytest nötig)
pytest tests/test_monitor.py -v # Mit pytest
```

11 Tests decken ab: ICMP-Erreichbarkeit, Port-Checks, Status-Logik (ONLINE/DEGRADED/OFFLINE), Mock-Tests für deterministisches Testen ohne echtes Netzwerk.

---

## Technische Entscheidungen

**Warum subprocess für Ping?** Das System-`ping`-Binary nutzt ICMP Raw Sockets, die Root-Rechte erfordern. Durch den Subprocess-Aufruf wird diese Komplexität an das OS delegiert und das Tool bleibt ohne Root lauffähig.

**Warum YAML für Konfiguration?** YAML ist in der IT-Welt (Ansible, Docker, Kubernetes) der De-facto-Standard für deklarative Konfiguration. Ein Admin kann die Geräteliste pflegen ohne Python zu kennen.

**Warum Docker mit `network_mode: host`?** ICMP-Pakete können nicht über das virtuelle Docker-Netzwerk geroutet werden. `host`-Modus gibt dem Container direkten Zugriff auf das physische Netzwerkinterface.

---

## Mögliche Erweiterungen

- E-Mail/Slack-Alert bei Statuswechsel (ONLINE -> OFFLINE)
- Grafana-Integration über Prometheus-Exporter
- Historische Auswertung der Response-Zeiten (Zeitreihendatenbank)
- Web-Frontend für Live-Status (Flask + HTMX)
- SNMP-Support für erweiterte Hardware-Metriken

---

## Autor

Portfolio-Projekt zur Demonstration von Fähigkeiten in Systemintegration, Netzwerkmonitoring und automatisiertem Deployment.  
Kontakt auf Anfrage.
