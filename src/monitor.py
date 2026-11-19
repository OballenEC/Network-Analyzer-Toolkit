# src/monitor.py
import json
import os
from datetime import datetime
from typing import List
from src.results_manager import DiagnosticResult

HISTORY_FILE = "reports/history.json"

def save_to_history(results: List[DiagnosticResult]):
    """Guarda los resultados en un historial para monitoreo continuo."""
    os.makedirs("reports", exist_ok=True)
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for r in results:
        if r.estado == "disponible":
            history.append({
                "timestamp": timestamp,
                "ip": r.ip,
                "latencia": r.latencia_promedio_ms
            })
            
    # Mantener solo los últimos 1000 registros para no llenar el disco
    history = history[-1000:]
    
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)
        
    return len(history)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []