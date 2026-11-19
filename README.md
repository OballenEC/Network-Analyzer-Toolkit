# 🌐 Network Diagnostic Toolkit (NDT)

![Python](https://img.shields.io/badge/Python-3.14-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.67-FF4B4B?style=flat-square&logo=streamlit)
![Tests](https://img.shields.io/badge/tests-31%20passed-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

**Autor:** Oscar Esteban Ballen Castellanos

Herramienta modular de diagnóstico de redes IPv4 con enfoque **NetDevOps**. Automatiza validación, descubrimiento de hosts, latencia, escaneo de puertos, DNS, traceroute, SSH/SNMP y exportación a Cisco Packet Tracer desde un dashboard web interactivo.

---

## 🎯 Características

- **Validación IPv4 robusta:** \ipaddress\, expansión de CIDR y deduplicación.
- **Motor ICMP concurrente:** \ThreadPoolExecutor\ para escaneo paralelo de subredes.
- **Traceroute integrado:** \ipscout\ para localizar dónde se pierde la conexión.
- **Análisis de latencia:** clasificación Excelente / Buena / Aceptable / Lenta con umbrales configurables.
- **Escaneo de puertos TCP:** detección de servicios comunes.
- **DNS Lookup:** resolución directa e inversa de nombres.
- **SSH / SNMP:** conectividad y consultas básicas a dispositivos de red.
- **Topología interactiva:** visualización con \pyvis\.
- **Exportación a Packet Tracer:** generación de archivo \.pkt\ con \pktlib\.
- **Historial de monitoreo:** registro de escaneos y comparación entre ejecuciones.
- **Dashboard con 3 pestañas:** Diagnóstico, NetDevOps e Historial.
- **Modo Real y Modo Demo:** datos reales o simulados.
- **Límite de seguridad:** 256 hosts por diagnóstico para evitar escaneos masivos.

---

## 🏗️ Arquitectura

\\\	ext
├── app.py                     # Interfaz Streamlit
├── config.py                  # Configuración global
├── requirements.txt           # Dependencias Python
├── LICENSE                    # Licencia MIT
├── CHANGELOG.md               # Historial de versiones
├── .gitignore                 # Archivos ignorados por Git
├── src/
│   ├── __init__.py
│   ├── validators.py          # Validación IPv4, CIDR, DNS
│   ├── network_engine.py      # ICMP, concurrencia, traceroute
│   ├── latency_analyzer.py    # Clasificación de latencias
│   ├── results_manager.py     # Estructuras de datos y resúmenes
│   ├── exporter.py            # Exportación CSV
│   ├── port_scanner.py        # Escaneo TCP concurrente
│   ├── topology.py            # Topología con PyVis
│   ├── packet_tracer_export.py# Exportación .pkt
│   ├── device_manager.py      # SSH (Netmiko) y SNMP (PySNMP)
│   └── monitor.py             # Historial de latencias
├── tests/                     # 31 tests unitarios
└── docs/
    ├── img/                   # Capturas de pantalla
    └── pytest_output.txt      # Salida de pruebas
\\\

---

## 🚀 Instalación

### Requisitos
- Python 3.14+
- Windows 11 / Linux / macOS
- Permisos de administrador para ICMP raw en Windows

### Pasos

\\\powershell
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/network-diagnostic-toolkit.git
cd network-diagnostic-toolkit

# 2. Crear entorno virtual
python -m venv venv
.\\venv\\Scripts\\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
streamlit run app.py
\\\

La aplicación estará disponible en \http://localhost:8501\.

---

## 📖 Uso

### Diagnóstico de red
1. Introduce IPs, dominios o rangos CIDR (ej. \8.8.8.8, 1.1.1.1, 192.168.1.0/24\).
2. Pulsa **▶ EJECUTAR DIAGNÓSTICO**.
3. Revisa métricas, tabla de resultados y topología.

### NetDevOps (SSH/SNMP)
1. Introduce IP, usuario y contraseña (SSH) o community (SNMP).
2. Pulsa **🔌 Probar SSH** o **📶 Probar SNMP**.
3. Revisa la salida y la lectura interpretativa.

### Historial
1. Ejecuta varios diagnósticos.
2. Revisa la evolución de latencias en la pestaña **📈 HISTORIAL**.

### Modo Demo
Selecciona **🟢 Demo (simulado)** en el sidebar para probar la interfaz sin enviar tráfico real.

---

## 🧪 Pruebas

\\\powershell
pytest -v
\\\

**Resultado esperado:** \31 passed\.

Cobertura actual: \alidators\, \latency_analyzer\, \exporter\, \
etwork_engine\.

---

## ⚠️ Limitaciones conocidas

- \	racert_host\ requiere permisos de administrador en Windows para ICMP raw.
- SNMPv1/v2c envía la community en texto plano. En producción se recomienda SNMPv3.
- La cobertura de tests se centra en módulos críticos; \port_scanner\, \	opology\, \device_manager\ y \monitor\ no tienen tests unitarios.
- El escaneo de puertos debe usarse solo en redes que controles.

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver \LICENSE\ para más detalles.

---

## 👤 Autor

**Oscar Esteban Ballen Castellanos**
- Desarrollador de software
- Enfoque: Python, redes, NetDevOps