"""
Unit-Tests für Network Monitor.
Ausführen: pytest tests/test_monitor.py -v
"""

import sys
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from monitor import ping_host, check_port, check_device, CheckResult


# ---------------------------------------------------------------------------
# ping_host
# ---------------------------------------------------------------------------

def test_ping_reachable_host():
    """Loopback (127.0.0.1) muss immer erreichbar sein."""
    ok, latency = ping_host("127.0.0.1")
    assert ok is True
    assert latency is not None
    assert latency >= 0


def test_ping_unreachable_host():
    """Host im nicht-gerouteten Bereich (TEST-NET) muss offline sein."""
    ok, latency = ping_host("192.0.2.1", timeout=1)
    assert ok is False
    assert latency is None


# ---------------------------------------------------------------------------
# check_port
# ---------------------------------------------------------------------------

def test_port_closed_on_loopback():
    """Port 1 auf Loopback ist mit sehr hoher Wahrscheinlichkeit geschlossen."""
    result = check_port("127.0.0.1", 1, timeout=0.3)
    assert isinstance(result, bool)


def test_port_check_returns_bool():
    """check_port gibt immer einen bool zurück, kein Exception."""
    result = check_port("192.0.2.1", 80, timeout=0.3)
    assert result is False


# ---------------------------------------------------------------------------
# CheckResult dataclass
# ---------------------------------------------------------------------------

def test_status_online():
    r = CheckResult("192.168.1.1", datetime.now(), True, 5.0, [80, 443], [])
    assert r.status == "ONLINE"


def test_status_degraded():
    r = CheckResult("192.168.1.1", datetime.now(), True, 5.0, [80], [443])
    assert r.status == "DEGRADED"


def test_status_offline():
    r = CheckResult("192.168.1.1", datetime.now(), False, None, [], [])
    assert r.status == "OFFLINE"


# ---------------------------------------------------------------------------
# check_device – mit Mock für schnelle Tests
# ---------------------------------------------------------------------------

def test_check_device_online():
    """Simuliert einen erreichbaren Host mit offenen Ports."""
    with patch("monitor.ping_host", return_value=(True, 3.5)), \
         patch("monitor.check_port", return_value=True):
        result = check_device("192.168.1.1", ports=[80, 443])
    assert result.ping_ok is True
    assert result.open_ports == [80, 443]
    assert result.closed_ports == []
    assert result.status == "ONLINE"


def test_check_device_offline():
    """Simuliert einen nicht erreichbaren Host – kein Port-Scan."""
    with patch("monitor.ping_host", return_value=(False, None)):
        result = check_device("192.168.1.99", ports=[80])
    assert result.ping_ok is False
    assert result.open_ports == []
    assert result.status == "OFFLINE"


def test_check_device_default_ports():
    """Ohne Port-Angabe werden Standard-Ports [22, 80, 443] geprüft."""
    with patch("monitor.ping_host", return_value=(True, 2.0)), \
         patch("monitor.check_port", return_value=True):
        result = check_device("127.0.0.1")
    assert set(result.open_ports) == {22, 80, 443}


def test_check_device_degraded():
    """Simuliert Host erreichbar aber ein Port geschlossen."""
    def mock_port(host, port, timeout=0.5):
        return port != 443  # Port 443 geschlossen

    with patch("monitor.ping_host", return_value=(True, 4.0)), \
         patch("monitor.check_port", side_effect=mock_port):
        result = check_device("192.168.1.1", ports=[80, 443])
    assert result.status == "DEGRADED"
    assert 443 in result.closed_ports
    assert 80 in result.open_ports


# ---------------------------------------------------------------------------
# Manueller Test-Runner (ohne pytest)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_ping_reachable_host,
        test_ping_unreachable_host,
        test_port_closed_on_loopback,
        test_port_check_returns_bool,
        test_status_online,
        test_status_degraded,
        test_status_offline,
        test_check_device_online,
        test_check_device_offline,
        test_check_device_default_ports,
        test_check_device_degraded,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} Tests bestanden.")
