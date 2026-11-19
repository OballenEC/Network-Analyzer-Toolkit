from typing import List, Optional

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
