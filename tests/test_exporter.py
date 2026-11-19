import csv
from src.results_manager import DiagnosticResult
from src.exporter import export_csv


def _make(ip="8.8.8.8", estado="disponible", lat=14.0):
    return DiagnosticResult(
        ip=ip, estado=estado, latencia_promedio_ms=lat,
        timestamp="2026-11-18 22:00:00", intentos=3,
        observaciones="3/3 respuestas",
        clasificacion="excelente", lento=False,
    )


class TestExporter:
    def test_creates_file(self, tmp_path):
        p = export_csv([_make()], path=tmp_path / "test.csv")
        assert p.exists()
    def test_headers(self, tmp_path):
        p = export_csv([_make()], path=tmp_path / "test.csv")
        with open(p, encoding="utf-8") as f:
            assert next(csv.reader(f)) == ["ip", "estado", "latencia_promedio_ms", "timestamp", "intentos", "observaciones"]
    def test_multiple_rows(self, tmp_path):
        p = export_csv([_make("8.8.8.8"), _make("1.1.1.1", "no_disponible", None)], path=tmp_path / "test.csv")
        with open(p, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[0]["ip"] == "8.8.8.8"
        assert rows[1]["estado"] == "no_disponible"
