import ipaddress
import socket
from typing import List, Tuple

def resolve_dns(hostname: str) -> str:
    """Intenta resolver un dominio a IP. Si falla o ya es IP, devuelve el original."""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return hostname


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
    tokens = raw.replace("\n", ",").replace(" ", ",").split(",")
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
