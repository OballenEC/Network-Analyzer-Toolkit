# src/packet_tracer_export.py
import pktlib
import ipaddress
from pathlib import Path
from src.results_manager import DiagnosticResult
from typing import List

def generate_pkt_topology(results: List[DiagnosticResult], output_path: str = "network_diagnostic_lab.pkt") -> Path:
    """
    Genera un archivo .pkt de Packet Tracer con una topología estrella.
    - Un switch central.
    - Un PC por cada host que respondió al diagnóstico.
    """
    net = pktlib.new()
    
    # 1. Crear el switch central
    switch = net.switch("SW1", at=(400, 300))
    
    # 2. Contador para posicionar los PCs
    x_offset = 0
    y_offset = 100
    
    # 3. Crear un PC por cada host disponible
    for i, r in enumerate(results):
        if r.estado == "disponible":
            pc_name = f"PC_{i+1}"
            ip_with_mask = f"{r.ip}/24" 
            
            # Calcular un gateway válido para esta IP específica
            try:
                # Creamos la red asumiendo máscara /24
                network = ipaddress.IPv4Network(ip_with_mask, strict=False)
                # El gateway será la primera IP usable de la red (ej: 192.168.1.1)
                gateway_ip = str(network.network_address + 1)
            except Exception:
                # Si algo falla (por ejemplo, es una IP inválida para PT), usamos uno por defecto
                gateway_ip = "192.168.1.1"
            
            pc = net.pc(
                pc_name, 
                at=(200 + x_offset, 450 + y_offset),
                ip=ip_with_mask,
                gateway=gateway_ip
            )
            
            # Conectar el PC al switch
            pc["fa0"].connect(switch[f"fa0/{i+1}"])
            
            # Ajustar offset para el siguiente PC
            x_offset += 150
    
    # 4. Guardar el archivo
    output_file = Path(output_path)
    net.save(str(output_file))
    return output_file