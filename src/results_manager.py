from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional

from src.network_engine import PingResult
from src.latency_analyzer import classify_latency, is_slow


@dataclass
class DiagnosticResult:
    ip: str
    estado: str
    latencia_promedio_ms: Optional[float]
    timestamp: str
    intentos: int
    observaciones: str
    clasificacion: str = ""
    lento: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def build_result(ping: PingResult) -> DiagnosticResult:
    lat = ping.latencia_promedio
    return DiagnosticResult(
        ip=ping.ip,
        estado="disponible" if ping.disponible else "no_disponible",
        latencia_promedio_ms=lat,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        intentos=ping.intentos,
        observaciones=ping.observaciones,
        clasificacion=classify_latency(lat),
        lento=is_slow(lat),
    )


def build_summary(results: List[DiagnosticResult]) -> dict:
    total = len(results)
    disponibles = sum(1 for r in results if r.estado == "disponible")
    latencias = [r.latencia_promedio_ms for r in results
                 if r.latencia_promedio_ms is not None]
    prom = round(sum(latencias) / len(latencias), 2) if latencias else None
    return {
        "total": total,
        "disponibles": disponibles,
        "no_disponibles": total - disponibles,
        "porcentaje_disponibilidad": round(
            (disponibles / total * 100) if total else 0, 1
        ),
        "latencia_promedio_ms": prom,
        "lentos": sum(1 for r in results if r.lento),
    }
