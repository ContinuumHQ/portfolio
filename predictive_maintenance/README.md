# Predictive Maintenance - Sensordaten-Pipeline

> **Portfolio-Projekt** | Software-Entwicklung / Data Engineering  
> Domäne: Medizintechnik-Fertigung · Predictive Maintenance  
> Stack: Python · Pandas · Matplotlib · Seaborn · Pytest

---

## Projektziel

Dieses Projekt demonstriert eine vollständige **Predictive-Maintenance-Pipeline** für
Produktionsmaschinen in der Medizintechnik. Es zeigt, wie man Rohdaten aus Sensoren
sammelt, bereinigt, feature-engineert und statistisch auswertet, um **Anomalien
frühzeitig zu erkennen** - bevor es zu einem Maschinenausfall kommt.

---

## Projektstruktur

```
predictive_maintenance/
│
├── main.py                  # Einstiegspunkt - orchestriert alle Schritte
├── data_generator.py        # Synthetische Rohdaten (Sensorsimulation)
├── pipeline.py              # Datenpipeline: Laden -> Bereinigen -> Features
├── anomaly_detection.py     # Z-Score & IQR Anomalieerkennung
├── visualization.py         # Dashboard-Plots (5 Visualisierungen)
│
├── tests/
│   └── test_pipeline.py     # Unit-Tests (pytest)
│
├── data/                    # Generierte CSV-Dateien (gitignore-fähig)
│   ├── raw_sensor_data.csv
│   ├── processed_sensor_data.csv
│   └── anomaly_scores.csv
│
├── docs/
│   └── plots/               # Alle erzeugten PNG-Visualisierungen
│
├── requirements.txt         # Reproduzierbare Umgebung (pip freeze)
└── README.md
```

---

## Architektur & Datenfluss

```
[data_generator.py]
    │  Simuliert 5.000+ Messungen für 4 Maschinen
    │  (Temperatur, Vibration, Druck, Zykluszeit, Betriebsstunden)
    ▼
[pipeline.py]
    │  1. load_data()         -> CSV laden, Typen validieren
    │  2. clean_data()        -> Duplikate, NaN, Clipping
    │  3. engineer_features() -> Rollende Statistiken, Differenzen
    ▼
[anomaly_detection.py]
    │  Z-Score   -> Abweichung vom Maschinenmittelwert (3-Sigma-Regel)
    │  IQR       -> Robuste Ausreißergrenze nach Tukey
    │  Combined  -> OR-Verknüpfung beider Methoden
    ▼
[visualization.py]
    │  5 Plots: Zeitreihe, Z-Score-Heatmap, IQR-Boxplots,
    │           Anomalie-Timeline, Korrelationsmatrix
    ▼
[docs/plots/*.png]
```

---

## Simulierte Maschinen & Sensoren

| Maschine        | Typ                             |
|-----------------|---------------------------------|
| `MED-INJ-01/02` | Injektionsformmaschine          |
| `MED-AUTO-01`   | Autoklav / Sterilisator         |
| `MED-PUMP-01`   | Hydraulikpumpe                  |

| Sensor           | Einheit | Normalbereich  | Anomalie-Faktor |
|------------------|---------|----------------|-----------------|
| `temperature_c`  | °C      | ~65 ± 2        | 1,4× - 2,2×     |
| `vibration_mm_s` | mm/s    | ~1,2 ± 0,15    | 1,4× - 2,2×     |
| `pressure_bar`   | bar     | ~6,5 ± 0,3     | 1,4× - 2,2×     |
| `cycle_time_s`   | s       | ~12,0 ± 0,5    | 1,4× - 2,2×     |

---

## Anomalieerkennung - Methodenwahl

### Z-Score

```
z = (x − μ) / σ
```

Ein Messwert gilt als Anomalie, wenn `|z| > 3` (3-Sigma-Regel).

**Stärken:** Schnell, intuitiv, reagiert sensitiv auf punktuelle Ausreißer.  
**Schwäche:** Mittelwert und Standardabweichung selbst werden durch Extremwerte
verzerrt - die Methode ist weniger robust bei bereits verschmutzten Datensätzen.

---

### IQR (Interquartilsabstand)

```
Untergrenze = Q1 − 1,5 · IQR
Obergrenze  = Q3 + 1,5 · IQR
IQR = Q3 − Q1
```

**Stärken:** Quartile sind robust gegenüber Extremwerten - einzelne Sensor-Spikes
(Messrauschen) beeinflussen die Grenzen kaum.  
**Ideal für:** Produktionsumgebungen mit häufigem Sensor-Rauschen.

---

### Kombiniertes Scoring (OR-Logik)

```python
anomaly_combined = anomaly_zscore | anomaly_iqr
```

Ein Datenpunkt gilt als Anomalie, wenn **mindestens eine** Methode anschlägt.
Diese konservative Verknüpfung priorisiert **Sensitivität** gegenüber Präzision -
ein vertretbarer Trade-off in der Medizintechnik, wo ein verpasster Defekt
schwerwiegender ist als ein Fehlalarm.

---

## Visualisierungen

| Nr. | Datei                         | Inhalt                                    |
|-----|-------------------------------|-------------------------------------------|
| 1   | `01_timeseries_*.png`         | Zeitreihenverlauf mit Anomalie-Markierung |
| 2   | `02_zscore_heatmap.png`       | Ø \|Z-Score\| pro Maschine & Sensor      |
| 3   | `03_iqr_boxplots.png`         | Verteilung Normal vs. Anomalie (IQR)      |
| 4   | `04_anomaly_timeline.png`     | Kumulierte Anomaliezählung über die Zeit  |
| 5   | `05_correlation_matrix.png`   | Pearson-Korrelation der Sensorsignale     |

---

## Schnellstart

### 1. Umgebung einrichten (reproduzierbar via `pip freeze`)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Pipeline ausführen

```bash
python main.py
```

Mit optionalen Parametern:

```bash
python main.py --samples 10000 --anomaly-rate 0.08 --seed 123
```

### 3. Tests ausführen

```bash
pytest tests/ -v
```

---

## Code-Qualität

| Kriterium         | Umsetzung                                                          |
|-------------------|--------------------------------------------------------------------|
| **PEP 8**         | Durchgehend eingehalten (Leerzeichen, Zeilenlänge, Namenskonvention)|
| **Docstrings**    | Alle Funktionen mit NumPy-Style Docstrings (Parameters, Returns)   |
| **Logging**       | `logging`-Modul statt `print()` - konfigurierbar, strukturiert     |
| **Reproduzierbarkeit** | `seed`-Parameter + `requirements.txt` via `pip freeze`       |
| **Testbarkeit**   | Einzelne, isolierte Funktionen + 15 Unit-Tests mit pytest          |
| **Erweiterbarkeit** | Pipeline-Schritte austauschbar, neue Sensoren/Maschinen trivial  |

---

## Mögliche Erweiterungen

- **ML-Modell:** Isolation Forest oder Autoencoder für nicht-parametrische Anomalieerkennung
- **Live-Dashboard:** Streamlit-Frontend für Echtzeit-Monitoring
- **Alerting:** E-Mail / Slack-Benachrichtigung bei kritischen Anomalien
- **Datenbankanbindung:** InfluxDB / TimescaleDB für echte Zeitreihendaten
- **CI/CD:** GitHub Actions für automatisierte Tests & Deployment

---

## Autor

Portfolio-Projekt zur Demonstration von Fähigkeiten in Data Engineering und Predictive Maintenance.  
Kontakt auf Anfrage.
