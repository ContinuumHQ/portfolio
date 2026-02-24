"""
Report-Generator für Network Monitor.
Erstellt strukturierte JSON-Logs und einen HTML-Statusbericht.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from monitor import CheckResult

logger = logging.getLogger(__name__)

REPORT_DIR = Path("docs")
REPORT_DIR.mkdir(exist_ok=True)


def results_to_dict(results: list[CheckResult]) -> list[dict]:
    """Konvertiert CheckResult-Objekte in JSON-serialisierbare Dicts."""
    return [
        {
            "host": r.host,
            "timestamp": r.timestamp.isoformat(),
            "status": r.status,
            "ping_ok": r.ping_ok,
            "ping_latency_ms": r.ping_latency_ms,
            "open_ports": r.open_ports,
            "closed_ports": r.closed_ports,
        }
        for r in results
    ]


def save_json_log(results: list[CheckResult], path: Path | None = None) -> Path:
    """
    Speichert Prüfergebnisse als JSON-Log.

    Parameters
    ----------
    results : list[CheckResult]
        Liste der Prüfergebnisse.
    path : Path, optional
        Zielpfad. Standard: docs/report_<timestamp>.json

    Returns
    -------
    Path
        Pfad zur gespeicherten Datei.
    """
    if path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = REPORT_DIR / f"report_{ts}.json"

    payload = {
        "generated_at": datetime.now().isoformat(),
        "total_hosts": len(results),
        "online": sum(1 for r in results if r.status == "ONLINE"),
        "degraded": sum(1 for r in results if r.status == "DEGRADED"),
        "offline": sum(1 for r in results if r.status == "OFFLINE"),
        "results": results_to_dict(results),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    logger.info("JSON-Report gespeichert: %s", path)
    return path


def save_html_report(results: list[CheckResult], path: Path | None = None) -> Path:
    """
    Erstellt einen übersichtlichen HTML-Statusbericht.

    Parameters
    ----------
    results : list[CheckResult]
        Liste der Prüfergebnisse.
    path : Path, optional
        Zielpfad. Standard: docs/report_<timestamp>.html

    Returns
    -------
    Path
        Pfad zur gespeicherten Datei.
    """
    if path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = REPORT_DIR / f"report_{ts}.html"

    status_colors = {"ONLINE": "#2ecc71", "DEGRADED": "#f39c12", "OFFLINE": "#e74c3c"}

    rows = ""
    for r in results:
        color = status_colors.get(r.status, "#bdc3c7")
        latency = f"{r.ping_latency_ms} ms" if r.ping_latency_ms else "—"
        open_p = ", ".join(str(p) for p in r.open_ports) or "—"
        closed_p = ", ".join(str(p) for p in r.closed_ports) or "—"
        rows += f"""
        <tr>
          <td>{r.host}</td>
          <td style="color:{color};font-weight:bold">{r.status}</td>
          <td>{latency}</td>
          <td>{open_p}</td>
          <td style="color:#e74c3c">{closed_p}</td>
          <td>{r.timestamp.strftime('%H:%M:%S')}</td>
        </tr>"""

    online = sum(1 for r in results if r.status == "ONLINE")
    offline = sum(1 for r in results if r.status == "OFFLINE")
    degraded = sum(1 for r in results if r.status == "DEGRADED")

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Network Monitor Report</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; margin: 0; padding: 20px; }}
    h1 {{ color: #00d4ff; border-bottom: 2px solid #00d4ff; padding-bottom: 8px; }}
    .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
    .card {{ background: #16213e; border-radius: 8px; padding: 16px 24px; text-align: center; min-width: 100px; }}
    .card .num {{ font-size: 2em; font-weight: bold; }}
    .card .label {{ font-size: 0.85em; color: #aaa; }}
    table {{ width: 100%; border-collapse: collapse; background: #16213e; border-radius: 8px; overflow: hidden; }}
    th {{ background: #0f3460; padding: 12px; text-align: left; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid #2a2a4a; }}
    tr:hover td {{ background: #1e3a5f; }}
    .ts {{ color: #888; font-size: 0.85em; margin-top: 20px; }}
  </style>
</head>
<body>
  <h1>🖧 Network Monitor — Statusbericht</h1>
  <div class="summary">
    <div class="card"><div class="num" style="color:#2ecc71">{online}</div><div class="label">ONLINE</div></div>
    <div class="card"><div class="num" style="color:#f39c12">{degraded}</div><div class="label">DEGRADED</div></div>
    <div class="card"><div class="num" style="color:#e74c3c">{offline}</div><div class="label">OFFLINE</div></div>
    <div class="card"><div class="num" style="color:#00d4ff">{len(results)}</div><div class="label">GESAMT</div></div>
  </div>
  <table>
    <thead>
      <tr><th>Host</th><th>Status</th><th>Latenz</th><th>Offene Ports</th><th>Geschlossene Ports</th><th>Zeit</th></tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <p class="ts">Generiert: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("HTML-Report gespeichert: %s", path)
    return path
