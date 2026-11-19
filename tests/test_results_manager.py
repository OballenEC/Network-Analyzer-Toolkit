from src.results_manager import DiagnosticResult, build_summary


class TestDiagnosticResult:
    def test_create(self):
        r = DiagnosticResult(
            ip='8.8.8.8',
            estado='disponible',
            latencia_promedio_ms=10.0,
            timestamp='12:00:00',
            intentos=3,
            observaciones='OK',
            clasificacion='excelente',
            lento=False,
        )
        assert r.ip == '8.8.8.8'
        assert r.estado == 'disponible'


class TestBuildSummary:
    def test_empty(self):
        summary = build_summary([])
        assert summary['total'] == 0
        assert summary['disponibles'] == 0

    def test_one_host(self):
        r = DiagnosticResult(
            ip='8.8.8.8', estado='disponible', latencia_promedio_ms=10.0,
            timestamp='12:00:00', intentos=3, observaciones='OK',
            clasificacion='excelente', lento=False,
        )
        summary = build_summary([r])
        assert summary['total'] == 1
        assert summary['disponibles'] == 1
        assert summary['porcentaje_disponibilidad'] == 100.0

    def test_mixed(self):
        r1 = DiagnosticResult(
            ip='8.8.8.8', estado='disponible', latencia_promedio_ms=10.0,
            timestamp='12:00:00', intentos=3, observaciones='OK',
            clasificacion='excelente', lento=False,
        )
        r2 = DiagnosticResult(
            ip='1.1.1.1', estado='no_disponible', latencia_promedio_ms=None,
            timestamp='12:00:00', intentos=3, observaciones='Timeout',
            clasificacion='—', lento=False,
        )
        summary = build_summary([r1, r2])
        assert summary['total'] == 2
        assert summary['disponibles'] == 1
        assert summary['no_disponibles'] == 1
        assert summary['porcentaje_disponibilidad'] == 50.0