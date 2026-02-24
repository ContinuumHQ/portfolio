"""
Network Monitor – Kernmodul
Prüft Erreichbarkeit (ICMP) und Port-Status von Netzwerkgeräten.
"""

import subprocess
import socket
import logging
import platform
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """Ergebnis einer einzelnen Geräteprüfung."""
    host: str
    timestamp: datetime
    ping_ok: bool
    ping_latency_ms: Optional[float]
    open_ports: list[int] = field(default_factory=list)
    closed_ports: list[int] = field(default_factory=list)

    @property
    def status(self) -> str:
        if not self.ping_ok:
            return "OFFLINE"
        if self.closed_ports:
            return "DEGRADED"
        return "ONLINE"


def ping_host(host: str, timeout: int = 1) -> tuple[bool, Optional[float]]:
    """
    Sendet einen ICMP-Ping an den angegebenen Host.

    Parameters
    ----------
    host : str
        Hostname oder IP-Adresse.
    timeout : int
        Timeout in Sekunden.

    Returns
    -------
    tuple[bool, Optional[float]]
        (erreichbar, Latenz in ms oder None)
    """
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_param = "-w" if platform.system().lower() == "windows" else "-W"

    cmd = ["ping", param, "1", timeout_param, str(timeout), host]

    try:
        start = datetime.now()
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 1
        )
        latency = (datetime.now() - start).total_seconds() * 1000
        if result.returncode == 0:
            return True, round(latency, 2)
        return False, None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, None


def check_port(host: str, port: int, timeout: float = 0.5) -> bool:
    """
    Prüft ob ein TCP-Port erreichbar ist.

    Parameters
    ----------
    host : str
        Ziel-Host.
    port : int
        Zu prüfender Port.
    timeout : float
        Verbindungs-Timeout in Sekunden.

    Returns
    -------
    bool
        True wenn Port offen, sonst False.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def check_device(host: str, ports: list[int] | None = None) -> CheckResult:
    """
    Führt eine vollständige Prüfung eines Netzwerkgeräts durch.

    Parameters
    ----------
    host : str
        Hostname oder IP-Adresse des Geräts.
    ports : list[int], optional
        Liste der zu prüfenden Ports. Standard: [22, 80, 443].

    Returns
    -------
    CheckResult
        Gesamtergebnis der Prüfung.
    """
    if ports is None:
        ports = [22, 80, 443]

    logger.info("Prüfe %s (Ports: %s)...", host, ports)
    ping_ok, latency = ping_host(host)

    open_ports, closed_ports = [], []
    if ping_ok:
        for port in ports:
            if check_port(host, port):
                open_ports.append(port)
            else:
                closed_ports.append(port)

    result = CheckResult(
        host=host,
        timestamp=datetime.now(),
        ping_ok=ping_ok,
        ping_latency_ms=latency,
        open_ports=open_ports,
        closed_ports=closed_ports,
    )
    logger.info("  → %s | Latenz: %s ms | Offen: %s | Geschlossen: %s",
                result.status, latency, open_ports, closed_ports)
    return result
