"""Escáner de puertos TCP básico (NetDevOps / Reconocimiento)."""
import socket
from typing import List

# Puertos comunes y su servicio asociado
COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    80: "HTTP",
    443: "HTTPS",
    3389: "RDP",
    8080: "HTTP-Alt"
}

def scan_ports(ip: str, timeout: float = 0.5) -> List[str]:
    """Escanea puertos comunes en una IP dada. Devuelve lista de 'Puerto (Servicio)'."""
    open_ports = []
    for port, service in COMMON_PORTS.items():
        # Creamos un socket TCP
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            # connect_ex devuelve 0 si el puerto está abierto
            result = s.connect_ex((ip, port))
            if result == 0:
                open_ports.append(f"{port} ({service})")
        except Exception:
            pass
        finally:
            s.close()
    return open_ports