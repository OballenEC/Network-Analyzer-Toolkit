from pathlib import Path

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
