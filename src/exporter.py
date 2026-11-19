import csv
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
