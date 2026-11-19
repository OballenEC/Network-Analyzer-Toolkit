import os
import tempfile
from unittest.mock import patch, MagicMock
from src.monitor import save_to_history, load_history


class TestMonitor:
    def test_save_and_load(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        try:
            mock_result = MagicMock()
            mock_result.ip = '8.8.8.8'
            mock_result.estado = 'disponible'
            mock_result.latencia_promedio_ms = 10.0
            mock_result.timestamp = '12:00:00'

            with patch('src.monitor.HISTORY_FILE', temp_path):
                save_to_history([mock_result])
                history = load_history()
                assert isinstance(history, list)
                assert len(history) >= 1
                assert history[0]['ip'] == '8.8.8.8'
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_load_empty(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        try:
            with patch('src.monitor.HISTORY_FILE', temp_path):
                history = load_history()
                assert history == []
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_load_nonexistent(self):
        with patch('src.monitor.HISTORY_FILE', '/ruta/que/no/existe.json'):
            history = load_history()
            assert history == []