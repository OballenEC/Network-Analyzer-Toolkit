from unittest.mock import patch, MagicMock
from src.port_scanner import scan_ports, COMMON_PORTS


class TestScanPorts:
    def test_signature(self):
        import inspect
        sig = inspect.signature(scan_ports)
        params = list(sig.parameters.keys())
        assert 'ip' in params
        assert 'timeout' in params

    def test_returns_list(self):
        result = scan_ports('127.0.0.1', timeout=0.1)
        assert isinstance(result, list)

    def test_common_ports_defined(self):
        # COMMON_PORTS es un dict {puerto: servicio}
        assert isinstance(COMMON_PORTS, dict)
        assert len(COMMON_PORTS) > 0
        assert all(isinstance(p, int) for p in COMMON_PORTS.keys())
        assert all(isinstance(s, str) for s in COMMON_PORTS.values())