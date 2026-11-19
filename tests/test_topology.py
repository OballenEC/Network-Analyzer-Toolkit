from unittest.mock import patch, MagicMock
from src.topology import render_topology


class TestRenderTopology:
    def test_empty_results(self):
        # No debe lanzar excepción con lista vacía
        try:
            render_topology([])
        except Exception as e:
            pytest.fail(f"render_topology([]) lanzó: {e}")

    def test_with_results(self):
        mock_result = MagicMock()
        mock_result.ip = '8.8.8.8'
        mock_result.estado = 'disponible'
        mock_result.latencia_promedio_ms = 10.0
        try:
            render_topology([mock_result])
        except Exception as e:
            pytest.fail(f"render_topology([result]) lanzó: {e}")