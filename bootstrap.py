"""Bootstrap: escribe todos los modulos del proyecto."""
from pathlib import Path

files = {}

files["requirements.txt"] = "streamlit>=1.40\npandas>=2.0\npytest>=8.0\n"
files[".gitignore"] = "venv/\n__pycache__/\n*.pyc\nreports/*.csv\n.vscode/\n.idea/\n.env\n.pytest_cache/\n"
files["conftest.py"] = "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent))\n"

files["config.py"] = '''from pathlib import Path

PING_ATTEMPTS = 3
PING_TIMEOUT_MS = 1000
SLOW_THRESHOLD_MS = 100.0

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

CSV_HEADERS = ["ip", "estado", "latencia_promedio_ms", "timestamp", "intentos", "observaciones"]

DEMO_RESULTS = [
    {"ip": "192.168.1.1", "disponible": True, "latencia": 8.2, "observaciones": "[DEMO] Gateway"},
    {"ip": "192.168.1.10", "disponible": True, "latencia": 25.4, "observaciones": "[DEMO] PC oficina"},
    {"ip": "192.168.1.25", "disponible": False, "latencia": None, "observaciones": "[DEMO] Impresora offline"},
    {"ip": "192.168.1.50", "disponible": True, "latencia": 142.7, "observaciones": "[DEMO] Servidor lento"},
    {"ip": "192.168.1.99", "disponible": False, "latencia": None, "observaciones": "[DEMO] Host desconectado"},
]
'''

files["src/__init__.py"] = '__version__ = "1.0.0"\n'

files["src/validators.py"] = '''import ipaddress
from typing import List, Tuple


class ValidationError(ValueError):
    pass


def validate_ip(ip_str: str) -> str:
    ip_str = (ip_str or "").strip()
    if not ip_str:
        raise ValidationError("IP vacia")
    try:
        return str(ipaddress.IPv4Address(ip_str))
    except ipaddress.AddressValueError as e:
        raise ValidationError(f"IPv4 invalida: {ip_str} ({e})")


def validate_list(raw: str) -> Tuple[List[str], List[str]]:
    if not raw or not raw.strip():
        return [], ["Entrada vacia"]
    tokens = raw.replace("\\n", ",").replace(" ", ",").split(",")
    validas, errores, vistas = [], [], set()
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        try:
            ip = validate_ip(tok)
            if ip not in vistas:
                vistas.add(ip)
                validas.append(ip)
        except ValidationError as e:
            errores.append(str(e))
    return validas, errores


def expand_range(spec: str) -> List[str]:
    spec = (spec or "").strip()
    if "/" in spec:
        net = ipaddress.IPv4Network(spec, strict=False)
        return [str(ip) for ip in net.hosts()]
    if "-" in spec:
        base, fin = spec.split("-", 1)
        base_ip = ipaddress.IPv4Address(base.strip())
        parts = str(base_ip).split(".")
        return [f"{parts[0]}.{parts[1]}.{parts[2]}.{i}"
                for i in range(int(parts[-1]), int(fin.strip()) + 1)]
    return [validate_ip(spec)]
'''

files["src/network_engine.py"] = '''import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

from config import PING_ATTEMPTS, PING_TIMEOUT_MS

RE_TIEMPO = re.compile(r"(?:tiempo|time)[=<]\\s*(\\d+)\\s*ms", re.IGNORECASE)


@dataclass
class PingResult:
    ip: str
    disponible: bool
    latencias: List[float] = field(default_factory=list)
    intentos: int = PING_ATTEMPTS
    observaciones: str = ""

    @property
    def latencia_promedio(self) -> Optional[float]:
        if not self.latencias:
            return None
        return round(sum(self.latencias) / len(self.latencias), 2)


def ping_host(ip: str, intentos: int = PING_ATTEMPTS,
              timeout_ms: int = PING_TIMEOUT_MS) -> PingResult:
    cmd = ["ping", "-n", str(intentos), "-w", str(timeout_ms), ip]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=(intentos * timeout_ms / 1000) + 5,
            encoding="cp1252", errors="ignore",
        )
    except FileNotFoundError:
        return PingResult(ip, False, observaciones="ping no disponible")
    except subprocess.TimeoutExpired:
        return PingResult(ip, False, observaciones="Timeout global")
    except Exception as e:
        return PingResult(ip, False, observaciones=f"Error: {e}")

    salida = (proc.stdout or "") + (proc.stderr or "")
    latencias = [float(m) for m in RE_TIEMPO.findall(salida)]
    recibidos = _extraer_recibidos(salida)

    if recibidos == 0 or not latencias:
        return PingResult(ip, False, observaciones=_clasificar_error(salida))

    return PingResult(
        ip=ip, disponible=True, latencias=latencias, intentos=intentos,
        observaciones=f"{len(latencias)}/{intentos} respuestas",
    )


def _extraer_recibidos(salida: str) -> int:
    m = re.search(r"(?:recibidos|received)\\s*[=]\\s*(\\d+)", salida, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def _clasificar_error(salida: str) -> str:
    s = salida.lower()
    if "inaccesible" in s or "unreachable" in s:
        return "Host inalcanzable"
    if "agotado" in s or "timed out" in s:
        return "Tiempo de espera agotado"
    if "no se puede encontrar" in s or "could not find" in s:
        return "Host no resuelto"
    return "Sin respuesta"
'''

files["src/latency_analyzer.py"] = '''from typing import List, Optional

from config import SLOW_THRESHOLD_MS


def classify_latency(ms: Optional[float]) -> str:
    if ms is None:
        return "sin_respuesta"
    if ms < 30:
        return "excelente"
    if ms < 100:
        return "buena"
    if ms < 200:
        return "aceptable"
    return "lenta"


def is_slow(ms: Optional[float]) -> bool:
    return ms is not None and ms > SLOW_THRESHOLD_MS


def average_latency(values: List[Optional[float]]) -> Optional[float]:
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 2)
'''

files["src/results_manager.py"] = '''from dataclasses import dataclass, asdict
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
'''

files["src/exporter.py"] = '''import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config import REPORTS_DIR, CSV_HEADERS
from src.results_manager import DiagnosticResult


def export_csv(results: List[DiagnosticResult],
               path: Optional[Path] = None) -> Path:
    if path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = REPORTS_DIR / f"diagnostico_{ts}.csv"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "ip": r.ip,
                "estado": r.estado,
                "latencia_promedio_ms": (
                    r.latencia_promedio_ms
                    if r.latencia_promedio_ms is not None else ""
                ),
                "timestamp": r.timestamp,
                "intentos": r.intentos,
                "observaciones": r.observaciones,
            })
    return path
'''

files["tests/__init__.py"] = ""

files["tests/test_validators.py"] = '''import pytest
from src.validators import validate_ip, validate_list, expand_range, ValidationError


class TestValidateIP:
    def test_valid_ip(self):
        assert validate_ip("8.8.8.8") == "8.8.8.8"
    def test_normalizes_whitespace(self):
        assert validate_ip("  1.1.1.1  ") == "1.1.1.1"
    def test_invalid_octet(self):
        with pytest.raises(ValidationError):
            validate_ip("999.1.1.1")
    def test_invalid_format(self):
        with pytest.raises(ValidationError):
            validate_ip("not-an-ip")
    def test_empty(self):
        with pytest.raises(ValidationError):
            validate_ip("")


class TestValidateList:
    def test_multiple_valid(self):
        v, e = validate_list("8.8.8.8, 1.1.1.1")
        assert v == ["8.8.8.8", "1.1.1.1"]
        assert e == []
    def test_deduplicates(self):
        v, _ = validate_list("8.8.8.8, 8.8.8.8, 1.1.1.1")
        assert v == ["8.8.8.8", "1.1.1.1"]
    def test_mixed_valid_invalid(self):
        v, e = validate_list("8.8.8.8, 999.1.1.1")
        assert v == ["8.8.8.8"]
        assert len(e) == 1
    def test_empty_input(self):
        v, e = validate_list("")
        assert v == []
        assert e


class TestExpandRange:
    def test_single_ip(self):
        assert expand_range("192.168.1.1") == ["192.168.1.1"]
    def test_range_last_octet(self):
        assert expand_range("192.168.1.1-3") == ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
    def test_cidr_slash_30(self):
        r = expand_range("192.168.1.0/30")
        assert "192.168.1.1" in r
        assert "192.168.1.2" in r
'''

files["tests/test_network_engine.py"] = '''from unittest.mock import patch, MagicMock
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
'''

files["tests/test_latency_analyzer.py"] = '''from src.latency_analyzer import classify_latency, is_slow, average_latency


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
'''

files["tests/test_exporter.py"] = '''import csv
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
'''

for rel, content in files.items():
    p = Path(rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"+ {rel}")

print(f"\n[OK] {len(files)} archivos escritos")