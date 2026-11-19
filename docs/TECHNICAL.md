# Documentación técnica — Network Diagnostic Toolkit (NDT)

## Arquitectura

### Flujo de datos

\\\	ext
Usuario → app.py → validators.py → network_engine.py → results_manager.py
                ↓
         latency_analyzer.py
                ↓
         exporter.py / topology.py / packet_tracer_export.py
                ↓
         monitor.py (historial)
\\\

### Módulos

| Módulo | Responsabilidad |
|--------|-----------------|
| \alidators.py\ | Validación IPv4, expansión CIDR, resolución DNS |
| \
etwork_engine.py\ | Ping concurrente (ICMP), traceroute |
| \latency_analyzer.py\ | Clasificación de latencia, detección de lentitud |
| \esults_manager.py\ | \DiagnosticResult\, \uild_result\, \uild_summary\ |
| \exporter.py\ | Exportación a CSV |
| \port_scanner.py\ | Escaneo TCP concurrente |
| \	opology.py\ | Topología interactiva con PyVis |
| \packet_tracer_export.py\ | Generación de \.pkt\ con pktlib |
| \device_manager.py\ | SSH (Netmiko) y SNMP (PySNMP) |
| \monitor.py\ | Guardado y carga de historial |

### Decisiones técnicas

- **Streamlit** para la interfaz: rápido, reactivo, sin necesidad de frontend separado.
- **ThreadPoolExecutor** para concurrencia: eficiente para ICMP y escaneo de puertos.
- **ipscout** para traceroute: multiplataforma, sin dependencias nativas.
- **pktlib** para Packet Tracer: única librería Python que genera \.pkt\ válidos.
- **pyvis** para topología: visualización interactiva basada en NetworkX.

### Limitaciones

- ICMP raw requiere permisos de administrador en Windows.
- SNMPv1/v2c en texto plano.
- Cobertura de tests parcial.

## Seguridad

- No se almacenan credenciales.
- SNMPv1/v2c advertido en el manual.
- Límite de 256 hosts por diagnóstico.
- Escaneo de puertos debe usarse solo en redes controladas.