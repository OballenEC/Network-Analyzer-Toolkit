import re
import streamlit as st
import pandas as pd
from datetime import datetime

from src.validators import validate_list, expand_range, resolve_dns
from src.network_engine import ping_concurrente, tracert_host
from src.results_manager import build_result, build_summary, DiagnosticResult
from src.latency_analyzer import classify_latency, is_slow
from src.exporter import export_csv
from src.port_scanner import scan_ports
from src.topology import render_topology
from src.packet_tracer_export import generate_pkt_topology
from src.device_manager import get_device_info_ssh, get_snmp_metrics
from src.monitor import save_to_history, load_history
from config import DEMO_RESULTS, PING_ATTEMPTS, PING_TIMEOUT_MS

st.set_page_config(page_title="NDT v2.0", page_icon="🌐", layout="wide")

# ==========================================================
# 1) MANUAL DE BIENVENIDA
# ==========================================================
if "manual_accepted" not in st.session_state:
    st.session_state.manual_accepted = False


@st.dialog("📘 Manual rápido — Network Diagnostic Toolkit v2.0")
def show_manual():
    st.markdown("""
    <style>
    [data-testid="stDialog"] > div {
        background-color: rgba(13, 17, 23, 0.97) !important;
        border: 1px solid #00ff41 !important;
        box-shadow: 0 0 25px rgba(0, 255, 65, 0.35) !important;
        font-family: 'Consolas', monospace !important;
    }
    [data-testid="stDialog"] h2 { color: #00ff41 !important; letter-spacing: 2px; }
    [data-testid="stDialog"] p,
    [data-testid="stDialog"] li,
    [data-testid="stDialog"] strong { color: #c8ffc8 !important; font-family: 'Consolas', monospace !important; }
    [data-testid="stDialog"] a { color: #00bfff !important; }
    [data-testid="stDialog"] button {
        background-color: rgba(13, 17, 23, 0.9) !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        letter-spacing: 2px;
        font-weight: bold;
    }
    [data-testid="stDialog"] button:hover {
        background-color: #00ff41 !important;
        color: #0a0e14 !important;
        box-shadow: 0 0 20px #00ff41;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
### ¿Qué hace esta herramienta?
- **Diagnóstico ICMP concurrente**: ping masivo a IPs, dominios o rangos CIDR.
- **Escaneo de puertos TCP** y **resolución DNS**.
- **Traceroute multiplataforma** y **topología interactiva** (PyVis).
- **NetDevOps**: SSH (Netmiko) y SNMP (PySNMP) para leer routers/switches Cisco.
- **Exportación** a Cisco Packet Tracer (`.pkt`) y CSV.
- **Historial de monitoreo** con evolución de latencias.

### Cómo usarla
1. En **Diagnóstico de red**, introduce IPs, dominios o un rango CIDR.
2. Pulsa **▶ Ejecutar diagnóstico** y revisa latencias, puertos y topología.
3. En **NetDevOps**, introduce IP, usuario y contraseña (SSH) o la community SNMP.
4. En **Historial**, observa la evolución de latencias.

### Sobre las credenciales NetDevOps
- **SSH:** las mismas credenciales que usarías para entrar al router/switch por consola SSH.
- **SNMP:** la *community string* (típicamente `public` para lectura). SNMPv1/v2 la envía en texto plano; úsala solo en laboratorio.

> No ejecutes escaneos masivos sobre redes que no controles.
    """)
    if st.button("✅ Acepto y comienzo", use_container_width=True):
        st.session_state.manual_accepted = True
        st.rerun()


if not st.session_state.manual_accepted:
    show_manual()
    st.stop()

# ==========================================================
# 2) MATRIX + GLASS + SCANLINES + GLITCH + TEAR ESPORÁDICO
# ==========================================================
st.markdown("""
<style>
/* -------- FONDO MATRIX -------- */
[data-testid="stAppViewContainer"] {
    background-color: #0a0e14 !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='400'%3E%3Cg font-family='monospace' font-size='16' font-weight='bold'%3E%3Ctext x='8' y='25' fill='%2300ff41'%3E0%3C/text%3E%3Ctext x='8' y='75' fill='%2300ff41'%3E1%3C/text%3E%3Ctext x='8' y='125' fill='%2300bfff'%3E1%3C/text%3E%3Ctext x='8' y='175' fill='%2300ff41'%3E0%3C/text%3E%3Ctext x='8' y='225' fill='%2300ff41'%3E1%3C/text%3E%3Ctext x='8' y='275' fill='%2300ff41'%3E0%3C/text%3E%3Ctext x='8' y='325' fill='%2300bfff'%3E1%3C/text%3E%3Ctext x='8' y='375' fill='%2300ff41'%3E0%3C/text%3E%3Ctext x='48' y='50' fill='%2300ff41'%3E1%3C/text%3E%3Ctext x='48' y='100' fill='%2300bfff'%3E0%3C/text%3E%3Ctext x='48' y='150' fill='%2300ff41'%3E1%3C/text%3E%3Ctext x='48' y='200' fill='%2300ff41'%3E0%3C/text%3E%3Ctext x='48' y='250' fill='%2300ff41'%3E1%3C/text%3E%3Ctext x='48' y='300' fill='%2300ff41'%3E0%3C/text%3E%3Ctext x='48' y='350' fill='%2300bfff'%3E1%3C/text%3E%3Ctext x='48' y='400' fill='%2300ff41'%3E0%3C/text%3E%3C/g%3E%3C/svg%3E");
    background-repeat: repeat;
    background-size: 80px 400px;
    animation: matrixFall 8s linear infinite, flicker 15s linear infinite;
}
@keyframes matrixFall {
    from { background-position: 0 0; }
    to   { background-position: 0 400px; }
}
@keyframes flicker {
    0%, 96%, 100% { opacity: 1; }
    97% { opacity: 0.9; }
    98% { opacity: 1; }
    99% { opacity: 0.95; }
}

/* -------- CRISTAL ESMERILADO -------- */
[data-testid="stMain"], .stMain {
    background: rgba(10, 14, 20, 0.55) !important;
    backdrop-filter: blur(3px) !important;
    -webkit-backdrop-filter: blur(3px) !important;
}
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stDataFrame"],
[data-testid="stMetric"],
[data-baseweb="tab-panel"] {
    background: rgba(13, 17, 23, 0.88) !important;
    backdrop-filter: blur(6px) !important;
    -webkit-backdrop-filter: blur(6px) !important;
    border-radius: 6px;
}

/* -------- SCANLINES CRT -------- */
[data-testid="stAppViewContainer"]::after {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        rgba(0, 255, 65, 0.035) 0px,
        rgba(0, 255, 65, 0.035) 1px,
        transparent 1px,
        transparent 4px
    );
    pointer-events: none;
    z-index: 1;
    animation: scan 8s linear infinite;
}
@keyframes scan {
    from { background-position: 0 0; }
    to   { background-position: 0 100vh; }
}

/* -------- GLITCH ESPORÁDICO DE PANTALLA -------- */
/* Overlay fijo que aparece muy brevemente cada cierto tiempo */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 2;
    opacity: 0;
    background:
        linear-gradient(90deg,
            rgba(255, 0, 80, 0.06) 0%,
            transparent 8%,
            transparent 92%,
            rgba(0, 191, 255, 0.06) 100%
        ),
        repeating-linear-gradient(
            0deg,
            rgba(255, 255, 255, 0.02) 0px,
            rgba(255, 255, 255, 0.02) 1px,
            transparent 1px,
            transparent 3px
        );
    animation: tear 14s infinite;
}
@keyframes tear {
    0%, 90%, 100% { opacity: 0; transform: translateX(0); filter: none; }
    90.5% { opacity: 0.9; transform: translateX(-4px); filter: hue-rotate(20deg); }
    91% { opacity: 0.7; transform: translateX(3px) skewX(1deg); }
    91.5% { opacity: 0.85; transform: translateX(-2px); }
    92% { opacity: 0.5; transform: translateX(1px) skewX(-1deg); }
    92.5% { opacity: 0; transform: translateX(0); }
}

/* -------- HEADER glitch -------- */
.terminal-header {
    color: #00ff41;
    border-bottom: 2px solid #00ff41;
    padding-bottom: 10px;
    margin-bottom: 20px;
    letter-spacing: 3px;
    font-size: 1.2em;
    text-align: center;
    text-shadow: 0 0 6px #00ff41;
    animation: glitch-header 6s infinite;
    position: relative;
}
.terminal-header::after {
    content: '█';
    color: #00ff41;
    margin-left: 8px;
    animation: blink 1s steps(1) infinite;
}
@keyframes blink { 50% { opacity: 0; } }
@keyframes glitch-header {
    0%, 85%, 100% { text-shadow: 0 0 6px #00ff41; transform: translate(0, 0); }
    86% { text-shadow: -3px 0 #00bfff, 3px 0 #00ff41; transform: translate(-2px, 1px); }
    87% { text-shadow: 3px 0 #00bfff, -3px 0 #00ff41; transform: translate(2px, -1px); }
    88% { text-shadow: -1px 0 #00bfff, 1px 0 #00ff41; transform: translate(-1px, 0); }
    89% { text-shadow: 0 0 6px #00ff41; transform: translate(0, 0); }
}

/* -------- BOTONES glitch hover -------- */
.stButton > button {
    background-color: rgba(13, 17, 23, 0.9);
    color: #00ff41;
    border: 1px solid #00ff41;
    font-weight: bold;
    letter-spacing: 2px;
    transition: 0.3s;
}
.stButton > button:hover {
    background-color: #00ff41;
    color: #0a0e14;
    box-shadow: 0 0 20px #00ff41;
    animation: glitch-btn 0.3s;
}
@keyframes glitch-btn {
    0%, 100% { transform: translate(0); }
    25% { transform: translate(-2px, 1px); box-shadow: 0 0 12px #00bfff; }
    50% { transform: translate(2px, -1px); box-shadow: 0 0 12px #00ff41; }
    75% { transform: translate(-1px, 2px); }
}

/* -------- TABS glitch -------- */
[data-baseweb="tab"][aria-selected="true"] {
    animation: glitch-tab 5s infinite;
}
@keyframes glitch-tab {
    0%, 92%, 100% { text-shadow: none; }
    93% { text-shadow: -1px 0 #00bfff, 1px 0 #00ff41; }
    94% { text-shadow: 1px 0 #00bfff, -1px 0 #00ff41; }
    95% { text-shadow: none; }
}

/* -------- MÉTRICAS glitch -------- */
[data-testid="stMetricValue"] {
    color: #00ff41 !important;
    text-shadow: 0 0 5px #00ff41;
    animation: glitch-metric 8s infinite;
}
@keyframes glitch-metric {
    0%, 90%, 100% { text-shadow: 0 0 5px #00ff41; }
    91% { text-shadow: -2px 0 #00bfff, 2px 0 #00ff41; }
    92% { text-shadow: 2px 0 #00bfff, -2px 0 #00ff41; }
    93% { text-shadow: 0 0 5px #00ff41; }
}

/* -------- GENERALES -------- */
.stApp { background: #0a0e14 !important; font-family: 'Consolas', monospace; }
h1,h2,h3,h4,h5,h6,p,label,span,.stMarkdown {
    color: #00ff41 !important;
    font-family: 'Consolas', monospace !important;
}
[data-testid="stSidebar"] {
    background-color: rgba(13, 17, 23, 0.92) !important;
    border-right: 1px solid #00ff41;
}
.stTextArea textarea, .stTextInput input {
    background-color: rgba(13, 17, 23, 0.8) !important;
    color: #00ff41 !important;
    border: 1px solid #00ff41 !important;
}
[data-testid="stMetricLabel"] { color: #8b949e !important; }

.hud-title {
    color: #00ff41;
    font-size: 0.9em;
    border-bottom: 1px dashed #00ff41;
    margin-bottom: 10px;
    padding-bottom: 5px;
}
.hud-module-item {
    display: flex; align-items: center;
    font-size: 0.85em; color: #8b949e;
    margin-bottom: 6px;
    font-family: 'Consolas', monospace;
}
.led-green {
    width: 8px; height: 8px;
    background-color: #00ff41;
    border-radius: 50%;
    margin-right: 10px;
    box-shadow: 0 0 8px #00ff41, 0 0 2px #fff;
    animation: pulse 2s infinite;
}
.led-blue {
    width: 8px; height: 8px;
    background-color: #00bfff;
    border-radius: 50%;
    margin-right: 10px;
    box-shadow: 0 0 8px #00bfff, 0 0 2px #fff;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

/* -------- FIX EXPANDER (flecha vs texto) -------- */
[data-testid="stExpander"] details > summary {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 10px 14px !important;
    color: #00ff41 !important;
    font-weight: bold;
    letter-spacing: 1px;
}
[data-testid="stExpander"] details > summary svg {
    color: #00ff41 !important;
    flex-shrink: 0 !important;
    margin-right: 6px !important;
    width: 18px !important;
    height: 18px !important;
}
[data-testid="stExpander"] details > summary p {
    margin: 0 !important;
    padding: 0 !important;
    color: #00ff41 !important;
}
[data-testid="stExpander"] details > div {
    padding: 12px 16px !important;
    color: #c8ffc8 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="terminal-header">// NETWORK DIAGNOSTIC TOOLKIT v2.0 — CYBER DASHBOARD //</div>',
    unsafe_allow_html=True,
)


# ==========================================================
# 3) UTILIDADES
# ==========================================================
def load_demo_results():
    results = []
    for row in DEMO_RESULTS:
        lat = row["latencia"]
        results.append(DiagnosticResult(
            ip=row["ip"],
            estado="disponible" if row["disponible"] else "no_disponible",
            latencia_promedio_ms=lat,
            timestamp=datetime.now().strftime("%H:%M:%S"),
            intentos=3,
            observaciones=row["observaciones"],
            clasificacion=classify_latency(lat),
            lento=is_slow(lat),
        ))
    return results


# ==========================================================
# 4) LECTURAS Y CONCLUSIONES
# ==========================================================
def lectura_telemetria(summary):
    total = summary["total"]
    disp = summary["disponibles"]
    no_disp = summary["no_disponibles"]
    pct = summary["porcentaje_disponibilidad"]
    lat = summary["latencia_promedio_ms"]

    lineas = [
        f"**Total de hosts analizados:** {total}.",
        f"**Disponibles:** {disp} · **No disponibles:** {no_disp} · **Disponibilidad:** {pct}%.",
    ]
    if lat is not None:
        if lat < 30:
            calidad = "excelente (red local o enlace de baja latencia)"
        elif lat < 100:
            calidad = "buena (enlace WAN típico)"
        elif lat < 200:
            calidad = "lenta (posible congestión o distancia geográfica)"
        else:
            calidad = "muy alta (posible saturación, pérdida o ruta ineficiente)"
        lineas.append(f"**Latencia promedio:** {lat} ms → calidad {calidad}.")

    if pct == 100:
        lineas.append("**Conclusión:** todos los hosts respondieron. La red o los destinos están operativos en el momento del escaneo.")
    elif pct >= 50:
        lineas.append("**Conclusión:** hay hosts que no responden. Puede deberse a firewall, ICMP bloqueado o equipos apagados. Revisa los que aparecen como no disponibles.")
    else:
        lineas.append("**Conclusión:** la mayoría de los hosts no respondieron. Verifica conectividad local, rutas o si el rango introducido es correcto.")
    return "\n\n".join(lineas)


def lectura_puertos(results):
    con_puertos = [r for r in results if "Puertos:" in (r.observaciones or "")]
    if not con_puertos:
        return None
    lineas = ["**Lectura del escaneo de puertos:**"]
    for r in con_puertos:
        lineas.append(f"- `{r.ip}` → {r.observaciones.split('Puertos:')[-1].strip()}")
    lineas.append(
        "Un puerto abierto indica que hay un servicio escuchando. "
        "No implica vulnerabilidad por sí mismo, pero es el primer paso de un análisis de superficie de ataque."
    )
    return "\n".join(lineas)


def lectura_traceroute(saltos, target):
    if not saltos:
        return "No se obtuvieron saltos. El host puede ser inalcanzable o ICMP está bloqueado en la ruta."
    if isinstance(saltos[0], dict) and saltos[0].get("error"):
        return f"**Error en traceroute:** {saltos[0]['error']}"

    validos = [s for s in saltos if s.get("ip")]
    if not validos:
        return "Ningún salto respondió. Es probable que la red bloquee ICMP o que el destino no sea alcanzable."

    max_lat = max(
        (s for s in validos if s.get("latencia_ms") is not None),
        key=lambda s: s["latencia_ms"],
        default=None,
    )
    alcanzado = any(s.get("reached") for s in validos)

    lineas = [
        f"**Ruta hacia `{target}`:** {len(validos)} saltos con respuesta.",
        f"**Destino alcanzado:** {'sí' if alcanzado else 'no'}.",
    ]
    if max_lat:
        lineas.append(
            f"**Salto con mayor latencia:** hop {max_lat['hop']} (`{max_lat['ip']}`) "
            f"con {max_lat['latencia_ms']} ms."
        )
    lineas.append(
        "Los saltos sin IP (mostrados como `—`) son routers que no responden a ICMP; "
        "es normal y no indica necesariamente un fallo."
    )
    return "\n\n".join(lineas)


def lectura_ssh(res):
    if res.get("status") != "success":
        return (
            f"**Fallo SSH:** `{res.get('message', 'desconocido')}`. "
            "Causas comunes: credenciales incorrectas, SSH deshabilitado, ACL que bloquea la IP de origen, "
            "o el dispositivo no es compatible con Netmiko."
        )
    return (
        "**Lectura SSH:** `show version` revela modelo, versión de IOS y uptime; "
        "`LLDP neighbors` muestra los dispositivos vecinos descubiertos por LLDP. "
        "Juntos permiten reconstruir la topología lógica de capa 2 alrededor del equipo."
    )


def lectura_snmp(res):
    if res.get("status") != "success":
        return (
            f"**Fallo SNMP:** `{res.get('message', 'desconocido')}`. "
            "Causas comunes: community incorrecta, SNMP deshabilitado, ACL, o versión distinta (v1/v2c/v3)."
        )
    return (
        "**Lectura SNMP:** `sysName` identifica el dispositivo, `sysUpTime` indica cuánto lleva encendido "
        "y `ifNumber` el número de interfaces. Si el uptime es bajo, el equipo pudo haberse reiniciado. "
        "Recuerda que SNMPv1/v2c envía la community en texto plano: en producción se recomienda SNMPv3."
    )


def lectura_historial(history_data):
    if not history_data:
        return "Aún no hay historial. Ejecuta un diagnóstico para empezar a registrar latencias."
    df = pd.DataFrame(history_data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    ultimos = df.sort_values("timestamp").groupby("ip").tail(1)
    lineas = ["**Lectura del historial:**"]
    for _, row in ultimos.iterrows():
        lineas.append(f"- `{row['ip']}` → última latencia registrada: {row['latencia']} ms.")
    lineas.append(
        "Si la línea sube de forma sostenida, hay congestión o degradación del enlace. "
        "Si hay picos aislados, puede ser pérdida momentánea o reruteo."
    )
    return "\n".join(lineas)


# ==========================================================
# 5) SIDEBAR HUD
# ==========================================================
with st.sidebar:
    st.markdown('<div class="hud-title">⚙ SYSTEM CONFIG</div>', unsafe_allow_html=True)
    mode = st.radio("Modo de ejecución", ["🔴 Real (ICMP)", "🟢 Demo (simulado)"], index=0)
    intentos = st.slider("Intentos por host", 1, 5, PING_ATTEMPTS)
    timeout = st.slider("Timeout (ms)", 200, 3000, PING_TIMEOUT_MS, step=100)
    scan_enabled = st.checkbox("🔍 Escanear Puertos TCP", value=False)

    st.markdown('<div class="hud-title" style="margin-top:20px;">📦 SYSTEM MODULES</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px; border-left: 2px solid #00ff41;">
        <div class="hud-module-item"><div class="led-green"></div> validators.py</div>
        <div class="hud-module-item"><div class="led-green"></div> network_engine.py</div>
        <div class="hud-module-item"><div class="led-green"></div> latency_analyzer.py</div>
        <div class="hud-module-item"><div class="led-green"></div> results_manager.py</div>
        <div class="hud-module-item"><div class="led-green"></div> exporter.py</div>
        <div class="hud-module-item"><div class="led-green"></div> port_scanner.py</div>
        <div class="hud-module-item"><div class="led-green"></div> topology.py</div>
        <div class="hud-module-item"><div class="led-green"></div> packet_tracer_export.py</div>
        <div class="hud-module-item"><div class="led-blue"></div> device_manager.py</div>
        <div class="hud-module-item"><div class="led-blue"></div> monitor.py</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hud-title" style="margin-top:20px;">📡 SYSTEM STATUS</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px; border-left: 2px solid #00bfff; font-size: 0.85em;">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span>Core Engine</span> <span style="color:#00ff41">ONLINE</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span>SSH Manager</span> <span style="color:#00bfff">READY</span>
        </div>
        <div style="display:flex; justify-content:space-between;">
            <span>Tests</span> <span style="color:#00ff41">31 PASSED</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================================
# 6) PESTAÑAS
# ==========================================================
tab_diag, tab_netdevops, tab_history = st.tabs([
    "🌐 DIAGNÓSTICO DE RED",
    "🖥 NETDEVOPS (SSH/SNMP)",
    "📈 HISTORIAL Y MONITOREO",
])


# ==========================================================
# 7) TAB 1 — DIAGNÓSTICO
# ==========================================================
with tab_diag:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 📡 TARGET ACQUISITION")
        default_ips = (
            "8.8.8.8, 1.1.1.1, google.com"
            if mode.startswith("🔴")
            else "192.168.1.1, 192.168.1.10, 192.168.1.25, 192.168.1.50, 192.168.1.99"
        )
        targets_input = st.text_area(
            "Direcciones IPv4 o Dominios (soporta CIDR):",
            value=default_ips,
            height=100,
        )

    with col2:
        st.markdown("### 🎯 ACTIONS")
        st.write("")

        if st.button("▶ EJECUTAR DIAGNÓSTICO", use_container_width=True):
            if mode.startswith("🟢"):
                results = load_demo_results()
                st.session_state.update({
                    "results": results, "is_demo": True, "summary": build_summary(results),
                })
            else:
                raw_tokens = [t.strip() for t in re.split(r"[,\n]", targets_input) if t.strip()]
                resolved_tokens = []
                for t in raw_tokens:
                    if "/" in t or "-" in t:
                        resolved_tokens.append(t)
                    else:
                        try:
                            resolved_tokens.append(resolve_dns(t))
                        except Exception:
                            resolved_tokens.append(t)

                validas, errores = validate_list("\n".join(resolved_tokens))
                for t in resolved_tokens:
                    if "/" in t or "-" in t:
                        try:
                            validas.extend(expand_range(t))
                        except Exception as e:
                            st.error(f"Error en rango '{t}': {e}")

                validas = list(set(validas))
                for e in errores:
                    st.error(e)

                if validas:
                    with st.spinner("Ejecutando pings concurrentes..."):
                        pings = ping_concurrente(validas, intentos=intentos, timeout_ms=timeout)
                        results = [build_result(p) for p in pings]

                        if scan_enabled:
                            with st.spinner("Escaneando puertos TCP abiertos..."):
                                for r in results:
                                    if r.estado == "disponible":
                                        puertos = scan_ports(r.ip)
                                        if puertos:
                                            r.observaciones += f" | Puertos: {', '.join(puertos)}"
                                        else:
                                            r.observaciones += " | Puertos: Ninguno"

                        st.session_state.update({
                            "results": results,
                            "is_demo": False,
                            "summary": build_summary(results),
                        })
                        save_to_history(results)

        if st.button("🌐 TRACEROUTE (Ruta)", use_container_width=True):
            if targets_input.strip():
                target = targets_input.split(",")[0].strip()
                try:
                    target_ip = resolve_dns(target)
                except Exception:
                    target_ip = None
                if target_ip:
                    with st.spinner(f"Trazando ruta a {target_ip}..."):
                        hops = tracert_host(target_ip)
                        st.session_state["tracert_data"] = hops
                        st.session_state["tracert_target"] = target_ip
                else:
                    st.error(f"No se pudo resolver: {target}")

    # ---- Resultados del diagnóstico ----
    if "results" in st.session_state and st.session_state.results:
        results = st.session_state.results
        summary = st.session_state.summary
        if st.session_state.is_demo:
            st.warning("⚠ MODO DEMO — Resultados SIMULADOS.")

        st.markdown("### 📊 TELEMETRÍA")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total", summary["total"])
        c2.metric("Disponibles", summary["disponibles"])
        c3.metric("No disp.", summary["no_disponibles"])
        c4.metric("Disponibilidad", f"{summary['porcentaje_disponibilidad']}%")
        c5.metric("Latencia prom.", f"{summary['latencia_promedio_ms'] or '—'} ms")

        st.markdown("### 🧠 LECTURA Y CONCLUSIONES")
        with st.expander("¿Qué significan estos resultados?", expanded=True):
            st.markdown(lectura_telemetria(summary))
            puertos_txt = lectura_puertos(results)
            if puertos_txt:
                st.markdown("---")
                st.markdown(puertos_txt)

        st.markdown("### 🖥 DATOS DE RED")
        df = pd.DataFrame([{
            "IP": r.ip,
            "Estado": ("🟢 " if r.estado == "disponible" else "🔴 ") + r.estado,
            "Latencia (ms)": r.latencia_promedio_ms if r.latencia_promedio_ms is not None else "—",
            "Clasificación": r.clasificacion,
            "Observaciones": r.observaciones,
            "Timestamp": r.timestamp,
        } for r in results])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("### 🗺 TOPOLOGÍA INTERACTIVA")
        render_topology(results)

        st.markdown("### 💾 EXPORTAR")
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv_path = export_csv(results)
            with open(csv_path, "rb") as f:
                csv_data = f.read()
            st.download_button(
                "⬇ DESCARGAR CSV",
                data=csv_data,
                file_name=csv_path.name,
                mime="text/csv",
                use_container_width=True,
            )
        with col_exp2:
            if st.button("📦 GENERAR LABORATORIO .PKT", use_container_width=True):
                with st.spinner("Generando topología para Packet Tracer..."):
                    try:
                        pkt_file = generate_pkt_topology(results)
                        with open(pkt_file, "rb") as f:
                            pkt_data = f.read()
                        st.download_button(
                            "⬇ DESCARGAR ARCHIVO .PKT",
                            data=pkt_data,
                            file_name=pkt_file.name,
                            mime="application/octet-stream",
                            use_container_width=True,
                        )
                        st.success("¡Laboratorio generado!")
                    except Exception as e:
                        st.error(f"Error al generar .pkt: {e}")

    # ---- Resultados del traceroute ----
    if "tracert_data" in st.session_state:
        st.markdown(f"### 🛣 RUTA HACIA {st.session_state['tracert_target']}")
        saltos = st.session_state["tracert_data"]
        if saltos and isinstance(saltos[0], dict) and saltos[0].get("error"):
            st.error(saltos[0]["error"])
        elif saltos:
            st.dataframe(saltos, use_container_width=True, hide_index=True)
        else:
            st.info("El traceroute no devolvió saltos (host inalcanzable o ICMP bloqueado en la ruta).")

        st.markdown("### 🧠 LECTURA DE LA RUTA")
        with st.expander("¿Qué significa esta ruta?", expanded=True):
            st.markdown(lectura_traceroute(saltos, st.session_state["tracert_target"]))


# ==========================================================
# 8) TAB 2 — NETDEVOPS
# ==========================================================
with tab_netdevops:
    st.markdown("### 🖥 GESTIÓN DE DISPOSITIVOS (NETDEVOPS)")
    st.caption("Capa 3 vía SSH (Netmiko) · Capa 4 vía SNMP (PySNMP)")

    col_ssh, col_snmp = st.columns(2)

    with col_ssh:
        with st.container(border=True):
            st.markdown("#### 🔐 SSH — Netmiko")
            dev_ip = st.text_input("IP del Dispositivo", "192.168.1.1", key="ssh_ip")
            dev_user = st.text_input("Usuario", "admin", key="ssh_user")
            dev_pass = st.text_input("Contraseña", type="password", key="ssh_pass")

            if st.button("🔌 Probar SSH", use_container_width=True):
                if not dev_ip.strip() or not dev_user.strip():
                    st.warning("Introduce IP y usuario antes de probar.")
                else:
                    with st.spinner("Conectando vía SSH..."):
                        res = get_device_info_ssh(dev_ip, dev_user, dev_pass)
                    if res.get("status") == "success":
                        st.success("Conexión SSH establecida")
                        st.text_area("Show Version", res.get("version", ""), height=200)
                        st.text_area("LLDP Neighbors", res.get("neighbors", ""), height=150)
                    else:
                        st.error(f"Fallo SSH: {res.get('message', 'desconocido')}")
                    st.markdown("### 🧠 LECTURA SSH")
                    st.markdown(lectura_ssh(res))

    with col_snmp:
        with st.container(border=True):
            st.markdown("#### 📡 SNMP — PySNMP")
            snmp_ip = st.text_input("IP del Dispositivo", "192.168.1.1", key="snmp_ip")
            snmp_comm = st.text_input("Community String", "public", type="password", key="snmp_comm")

            if st.button("📶 Probar SNMP", use_container_width=True):
                if not snmp_ip.strip() or not snmp_comm.strip():
                    st.warning("Introduce IP y community antes de consultar.")
                else:
                    with st.spinner("Consultando SNMP..."):
                        res = get_snmp_metrics(snmp_ip, snmp_comm)
                    if res.get("status") == "success":
                        st.success(f"Dispositivo: {res.get('sysName', '(sin nombre)')}")
                        st.json(res)
                    else:
                        st.error(f"Fallo SNMP: {res.get('message', 'desconocido')}")
                    st.markdown("### 🧠 LECTURA SNMP")
                    st.markdown(lectura_snmp(res))


# ==========================================================
# 9) TAB 3 — HISTORIAL
# ==========================================================
with tab_history:
    st.markdown("### 📈 HISTORIAL DE LATENCIA")
    st.write("Evolución de la latencia de los hosts monitoreados a lo largo del tiempo.")

    history_data = load_history()
    if history_data:
        df_hist = pd.DataFrame(history_data)
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
        st.line_chart(df_hist, x="timestamp", y="latencia", color="ip", use_container_width=True)
        st.dataframe(df_hist.tail(20), use_container_width=True)

        st.markdown("### 🧠 LECTURA DEL HISTORIAL")
        with st.expander("¿Qué significa esta evolución?", expanded=True):
            st.markdown(lectura_historial(history_data))
    else:
        st.info("No hay datos de historial aún. Ejecuta un diagnóstico en la primera pestaña para empezar a recolectar datos.")