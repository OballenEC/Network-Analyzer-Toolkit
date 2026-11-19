from unittest.mock import patch, MagicMock
from src.device_manager import get_device_info_ssh, get_snmp_metrics


class TestDeviceManager:
    def test_ssh_import(self):
        assert callable(get_device_info_ssh)

    def test_snmp_import(self):
        assert callable(get_snmp_metrics)

    def test_ssh_invalid_credentials(self):
        with patch('src.device_manager.ConnectHandler') as mock_conn:
            mock_conn.side_effect = Exception('Auth failed')
            result = get_device_info_ssh('192.168.1.1', 'user', 'wrong')
            assert result['status'] == 'error'

    def test_snmp_invalid_community(self):
        # Llamada real a localhost sin agente SNMP → debe devolver status error
        result = get_snmp_metrics('127.0.0.1', 'invalid_community')
        assert isinstance(result, dict)
        assert 'status' in result
        assert result['status'] == 'error'