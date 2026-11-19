# 🌐 Network Diagnostic Toolkit (NDT) v2.0

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40-FF4B4B?style=flat-square&logo=streamlit)
![Tests](https://img.shields.io/badge/tests-31%20passed-brightgreen?style=flat-square)
![Focus](https://img.shields.io/badge/Focus-NetDevOps-purple?style=flat-square)

**Autor:** Oscar Esteban Ballen Castellanos — Desarrollador de software

Herramienta modular de diagnóstico de redes IPv4 con enfoque **NetDevOps**. Automatiza validación, descubrimiento de hosts, latencia, escaneo de puertos, DNS, traceroute, SSH/SNMP y export a Cisco Packet Tracer desde un dashboard web interactivo.

## 🎯 Características

### v1.0
- **Validación IPv4 robusta:** `ipaddress`, expansión de CIDR y deduplicación.
- **Motor ICMP concurrente:** `ThreadPoolExecutor` para escaneo paralelo de subredes.
- **Traceroute integrado:** `tracert` nativo para localizar dónde se pierde la conexión.
- **Análisis de latencia:** Clasificación Excelente / Buena / Lenta con umbrales configurables.
- **Modo DEMO:** Escenario simulado, claramente etiquetado.

### v2.0 (nuevo)
- **Port Scanner concurrente:** Puertos TCP con detección de servicios comunes.
- **DNS Lookup:** Resolución directa e inversa de nombres.
- **SSH / SNMP:** Conectividad y consultas básicas a dispositivos de red.
- **Topología interactiva con PyVis:** Visualización de saltos del traceroute y hosts activos.
- **Export a Packet Tracer:** Generación de archivo `.pkt` del laboratorio.
- **Historial de monitoreo:** Registro de escaneos y comparación entre ejecuciones.
- **Dashboard con 3 pestañas:** Diagnóstico, Topología y Administración.
- **Matrix rain + HUD sidebar:** Experiencia visual cyberpunk.

## 🏗️ Arquitectura

```text
├── app.py                  # Interfaz de usuario (Streamlit)
├── config.py               # Configuración global
├── bootstrap.py            # Arranque y utilidades
├── src/
│   ├── validators.py       # Validación IPv4 y expansión CIDR
│   ├── network_engine.py   # ICMP, concurrencia, Traceroute
│   ├── latency_analyzer.py # Clasificación de latencias
│   ├── results_manager.py  # Estructuras de datos y resúmenes
│   └── exporter.py         # Exportación de reportes
├── tests/                  # 31 tests unitarios con mocks
├── packages.txt            # Dependencias de sistema (libpcap-dev)
└── requirements.txt        # Dependencias Python