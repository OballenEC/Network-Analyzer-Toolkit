import re
import subprocess
import concurrent.futures
from dataclasses import dataclass, field
from typing import List, Optional
from config import PING_ATTEMPTS, PING_TIMEOUT_MS

RE_TIEMPO = re.compile(r"(?:tiempo|time)[=<]\s*(\d+)\s*ms", re.IGNORECASE)

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

def ping_host(ip: str, intentos: int = PING_ATTEMPTS, timeout_ms: int = PING_TIMEOUT_MS) -> PingResult:
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

def ping_concurrente(ips: List[str], intentos: int = PING_ATTEMPTS, timeout_ms: int = PING_TIMEOUT_MS) -> List[PingResult]:
    resultados = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futuros = {executor.submit(ping_host, ip, intentos, timeout_ms): ip for ip in ips}
        for futuro in concurrent.futures.as_completed(futuros):
            resultados.append(futuro.result())
    return resultados

def tracert_host(ip: str, max_hops: int = 15) -> List[str]:
    cmd = ["tracert", "-h", str(max_hops), "-w", "1000", ip]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding="cp1252", errors="ignore")
        return (proc.stdout or "").strip().split("\n")
    except Exception as e:
        return [f"Error ejecutando tracert: {e}"]

def _extraer_recibidos(salida: str) -> int:
    m = re.search(r"(?:recibidos|received)\s*[=]\s*(\d+)", salida, re.IGNORECASE)
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