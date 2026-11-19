from unittest.mock import patch, MagicMock
from src.network_engine import ping_host, _extraer_recibidos, _clasificar_error


SALIDA_OK = """
Respuesta desde 8.8.8.8: bytes=32 tiempo=14ms TTL=117
Respuesta desde 8.8.8.8: bytes=32 tiempo=13ms TTL=117
Respuesta desde 8.8.8.8: bytes=32 tiempo=15ms TTL=117
Paquetes: enviados = 3, recibidos = 3, perdidos = 0
"""

SALIDA_TIMEOUT = """
Tiempo de espera agotado para esta solicitud.
Paquetes: enviados = 3, recibidos = 0, perdidos = 3
"""


class TestPingHostMocked:
    @patch("src.network_engine.subprocess.run")
    def test_host_disponible(self, mock_run):
        mock_run.return_value = MagicMock(stdout=SALIDA_OK, stderr="", returncode=0)
        r = ping_host("8.8.8.8")
        assert r.disponible is True
        assert r.latencias == [14.0, 13.0, 15.0]
        assert r.latencia_promedio == 14.0
    @patch("src.network_engine.subprocess.run")
    def test_host_timeout(self, mock_run):
        mock_run.return_value = MagicMock(stdout=SALIDA_TIMEOUT, stderr="", returncode=1)
        r = ping_host("192.0.2.1")
        assert r.disponible is False
        assert r.latencia_promedio is None


class TestHelpers:
    def test_extraer_recibidos_ok(self):
        assert _extraer_recibidos(SALIDA_OK) == 3
    def test_extraer_recibidos_timeout(self):
        assert _extraer_recibidos(SALIDA_TIMEOUT) == 0
    def test_clasificar_timeout(self):
        assert "espera" in _clasificar_error(SALIDA_TIMEOUT).lower()
