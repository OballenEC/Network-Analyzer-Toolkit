# Changelog — Network Diagnostic Toolkit (NDT)

## [1.0.0] — 2026-11-19

### Añadido
- Diagnóstico ICMP concurrente (ping masivo).
- Validación de IPv4 y rangos CIDR.
- Análisis de latencia con clasificación (excelente, buena, aceptable, lenta).
- Escaneo de puertos TCP.
- Traceroute multiplataforma con ipscout.
- Modo Real y Modo Demo.
- Exportación a CSV.
- Exportación a Cisco Packet Tracer (.pkt) con pktlib.
- Topología interactiva con pyvis.
- Gestión de dispositivos vía SSH (netmiko).
- Consultas SNMP (pysnmp).
- Historial de latencias.
- Interfaz Streamlit con 3 pestañas.
- Manual de bienvenida con aceptación obligatoria.
- Límite de 256 hosts por diagnóstico para evitar escaneos masivos.

### Conocido
- tracert_host requiere permisos de administrador en Windows para ICMP raw.
- SNMPv1/v2c envía la community en texto plano.
- La cobertura de tests se centra en validators, latency_analyzer, exporter y network_engine.