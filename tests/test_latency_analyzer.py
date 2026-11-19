from src.latency_analyzer import classify_latency, is_slow, average_latency


class TestClassifyLatency:
    def test_none(self):
        assert classify_latency(None) == "sin_respuesta"
    def test_excelente(self):
        assert classify_latency(15.0) == "excelente"
    def test_buena(self):
        assert classify_latency(50.0) == "buena"
    def test_aceptable(self):
        assert classify_latency(150.0) == "aceptable"
    def test_lenta(self):
        assert classify_latency(250.0) == "lenta"


class TestIsSlow:
    def test_none(self):
        assert is_slow(None) is False
    def test_under(self):
        assert is_slow(50.0) is False
    def test_over(self):
        assert is_slow(150.0) is True


class TestAverageLatency:
    def test_empty(self):
        assert average_latency([]) is None
    def test_all_none(self):
        assert average_latency([None, None]) is None
    def test_mixed(self):
        assert average_latency([10.0, 20.0, None]) == 15.0
