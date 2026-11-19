import streamlit as st
import streamlit.components.v1 as components
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

st.set_page_config(page_title="NDT v1.0", page_icon="🌐", layout="wide")

# ... (Todo el bloque de matrix_js y CSS se mantiene igual) ...
matrix_js = """
<script>
const canvas = document.createElement('canvas');
canvas.style.position = 'fixed'; canvas.style.top = '0'; canvas.style.left = '0';
canvas.style.width = '100vw'; canvas.style.height = '100vh'; canvas.style.zIndex = '-1';
canvas.style.pointerEvents = 'none';
document.body.appendChild(canvas);
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth; canvas.height = window.innerHeight;
const chars = '01'.split('');
const fontSize = 16; const columns = canvas.width / fontSize;
const drops = []; for(let x = 0; x < columns; x++) drops[x] = 1;
function draw() {
    ctx.fillStyle = 'rgba(10, 14, 20, 0.1)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#00ff41'; ctx.font = fontSize + 'px monospace';
    for(let i = 0; i < drops.length; i++) {
        const text = chars[Math.floor(Math.random() * chars.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);
        if(drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
    }
}
setInterval(draw, 50);
</script>
"""
components.html(matrix_js, height=0)

st.markdown("""
<style>
.stApp { background: transparent !important; font-family: 'Consolas', monospace; }
h1,h2,h3,h4,h5,h6,p,label,span,.stMarkdown { color: #00ff41 !important; font-family: 'Consolas', monospace !important; }
[data-testid="stSidebar"] { background-color: rgba(13, 17, 23, 0.9) !important; border-right: 1px solid #00ff41; }
.stTextArea textarea,.stTextInput input { background-color: rgba(13, 17, 23, 0.8) !important; color:#00ff41 !important; border:1px solid #00ff41 !important; }
.stButton>button { background-color:rgba(13, 17, 23, 0.9); color:#00ff41; border:1px solid #00ff41; font-weight:bold; letter-spacing:2px; transition: 0.3s; }
.stButton>button:hover { background-color:#00ff41; color:#0a0e14; box-shadow:0 0 20px #00ff41; }
[data-testid="stMetricValue"] { color:#00ff41 !important; text-shadow: 0 0 5px #00ff41; }
[data-testid="stMetricLabel"] { color:#8b949e !important; }
.terminal-header { color:#00ff41; border-bottom:2px solid #00ff41; padding-bottom:10px; margin-bottom:20px; letter-spacing:3px; font-size:1.2em; text-align:center; }
.hud-panel { background-color: rgba(13, 17, 23, 0.7); border: 1px solid #00ff41; padding: 15px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 0 10px rgba(0,255,65,0.2); }
.hud-title { color: #00ff41; font-size: 0.9em; border-bottom: 1px dashed #00ff41; margin-bottom: 10px; padding-bottom: 5px; }
.hud-module-item { display: flex; align-items: center; font-size: 0.85em; color: #8b949e; margin-bottom: 6px; font-family: 'Consolas', monospace; }
.led-green { width: 8px; height: 8px; background-color: #00ff41; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 8px #00ff41, 0 0 2px #fff; animation: pulse 2s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="terminal-header">// NETWORK DIAGNOSTIC TOOLKIT v1.0 — CYBER DASHBOARD //</div>', unsafe_allow_html=True)

def load_demo_results():
    results = []
    for row in DEMO_RESULTS:
        lat = row["latencia"]
        results.append(DiagnosticResult(
            ip=row["ip"], estado="disponible" if row["disponible"] else "no_disponible",
            latencia_promedio_ms=lat, timestamp=datetime.now().strftime("%H:%M:%S"),
            intentos=3, observaciones=row["observaciones"], clasificacion=classify_latency(lat), lento=is_slow(lat)
        ))
    return results

# --- SIDEBAR HUD ---
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
        <div class="hud-module-item"><div class="led-green"></div> packet_tracer.py</div>
        <div class="hud-module-item"><div class="led-green"></div> device_manager.py</div>
        <div class="hud-module-item"><div class="led-green"></div> monitor.py</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="hud-title" style="margin-top:20px;">📡 SYSTEM STATUS</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px; border-left: 2px solid #00ff41; font-size: 0.85em;">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span>Core Engine</span> <span style="color:#00ff41">ONLINE</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span>SSH Manager</span> <span style="color:#00ff41">READY</span>
        </div>
        <div style="display:flex; justify-content:space-between;">
            <span>Tests</span> <span style="color:#00ff41">31 PASSED</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- PESTAÑAS PRINCIPALES ---
tab_diag, tab_netdevops, tab_history = st.tabs(["🌐 DIAGNÓSTICO DE RED", "🖥 NETDEVOPS (SSH/SNMP)", "📈 HISTORIAL Y MONITOREO"])

# --- TAB 1: DIAGNÓSTICO (Lo que ya teníamos) ---
with tab_diag:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 📡 TARGET ACQUISITION")
        default_ips = ("8.8.8.8, 1.1.1.1, google.com" if mode.startswith("🔴") 
                       else "192.168.1.1, 192.168.1.10, 192.168.1.25, 192.168.1.50, 192.168.1.99")
        targets_input = st.text_area("Direcciones IPv4 o Dominios (soporta CIDR):", value=default_ips, height=100)

    with col2:
        st.markdown("### 🎯 ACTIONS")
        st.write("") 
        if st.button("▶ EJECUTAR DIAGNÓSTICO", use_container_width=True):
            if mode.startswith("🟢"):
                results = load_demo_results()
                st.session_state.update({"results": results, "is_demo": True, "summary": build_summary(results)})
            else:
                validas, errores = validate_list(targets_input)
                validas = [resolve_dns(ip) for ip in validas]
                
                if "/" in targets_input or "-" in targets_input:
                    try:
                        validas.extend(expand_range(targets_input))
                        validas = list(set(validas)) 
                    except Exception as e:
                        st.error(f"Error en rango: {e}")
                
                for e in errores: st.error(e)
                
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
                        
                        st.session_state.update({"results": results, "is_demo": False, "summary": build_summary(results)})
                        save_to_history(results) # Guardamos automáticamente en el historial
                        
        if st.button("🌐 TRACEROUTE (Ruta)", use_container_width=True):
            if targets_input.strip():
                target = targets_input.split(",")[0].strip()
                target_ip = resolve_dns(target)
                with st.spinner(f"Trazando ruta a {target_ip}..."):
                    hops = tracert_host(target_ip)
                    st.session_state["tracert_out"] = "\n".join(hops)
                    st.session_state["tracert_target"] = target_ip

    if "results" in st.session_state and st.session_state.results:
        results = st.session_state.results
        summary = st.session_state.summary
        if st.session_state.is_demo:
            st.warning("⚠ MODO DEMO — Resultados SIMULADOS.")

        st.markdown("### 📊 TELEMETRÍA")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total", summary["total"]); c2.metric("Disponibles", summary["disponibles"])
        c3.metric("No disp.", summary["no_disponibles"]); c4.metric("Disponibilidad", f"{summary['porcentaje_disponibilidad']}%")
        c5.metric("Latencia prom.", f"{summary['latencia_promedio_ms'] or '—'} ms")

        st.markdown("### 🖥 DATOS DE RED")
        df = pd.DataFrame([{
            "IP": r.ip, "Estado": ("🟢 " if r.estado == "disponible" else "🔴 ") + r.estado,
            "Latencia (ms)": r.latencia_promedio_ms if r.latencia_promedio_ms is not None else "—",
            "Clasificación": r.clasificacion, "Observaciones": r.observaciones, "Timestamp": r.timestamp,
        } for r in results])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("### 🗺 TOPOLOGÍA INTERACTIVA")
        render_topology(results)

        st.markdown("### 💾 EXPORTAR")
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv_path = export_csv(results)
            with open(csv_path, "rb") as f: csv_data = f.read()
            st.download_button("⬇ DESCARGAR CSV", data=csv_data, file_name=csv_path.name, mime="text/csv", use_container_width=True)
        with col_exp2:
            if st.button("📦 GENERAR LABORATORIO .PKT", use_container_width=True):
                with st.spinner("Generando topología para Packet Tracer..."):
                    try:
                        pkt_file = generate_pkt_topology(results)
                        with open(pkt_file, "rb") as f:
                            st.download_button("⬇ DESCARGAR ARCHIVO .PKT", data=f, file_name=pkt_file.name, mime="application/octet-stream", use_container_width=True)
                        st.success(f"¡Laboratorio generado!")
                    except Exception as e:
                        st.error(f"Error al generar .pkt: {e}")

    if "tracert_out" in st.session_state:
        st.markdown(f"### 🛣 RUTA HACIA {st.session_state['tracert_target']}")
        st.code(st.session_state["tracert_out"], language="bash")

# --- TAB 2: NETDEVOPS (SSH / SNMP) ---
with tab_netdevops:
    st.markdown("### 🖥 GESTIÓN DE DISPOSITIVOS (NETDEVOPS)")
    st.write("Conéctate a routers o switches Cisco para leer su configuración (Capa 3) o métricas SNMP (Capa 4).")
    
    col_ssh1, col_ssh2 = st.columns(2)
    with col_ssh1:
        st.markdown("#### 🔐 SSH (Netmiko)")
        dev_ip = st.text_input("IP del Dispositivo", "192.168.1.1")
        dev_user = st.text_input("Usuario", "admin")
        dev_pass = st.text_input("Contraseña", type="password")
        if st.button("Probar SSH", use_container_width=True):
            with st.spinner("Conectando vía SSH..."):
                res = get_device_info_ssh(dev_ip, dev_user, dev_pass)
                if res["status"] == "success":
                    st.success("Conexión Exitosa")
                    st.text_area("Show Version", res["version"], height=200)
                    st.text_area("LLDP Neighbors", res["neighbors"], height=150)
                else:
                    st.error(f"Fallo SSH: {res['message']}")
    
    with col_ssh2:
        st.markdown("#### 📡 SNMP (PySNMP)")
        snmp_ip = st.text_input("IP del Dispositivo (SNMP)", "192.168.1.1")
        snmp_comm = st.text_input("Community String", "public")
        if st.button("Probar SNMP", use_container_width=True):
            with st.spinner("Consultando SNMP..."):
                res = get_snmp_metrics(snmp_ip, snmp_comm)
                if res["status"] == "success":
                    st.success(f"Dispositivo: {res['sysName']}")
                else:
                    st.error(f"Fallo SNMP: {res['message']}")

# --- TAB 3: HISTORIAL Y MONITOREO ---
with tab_history:
    st.markdown("### 📈 HISTORIAL DE LATENCIA")
    st.write("Evolución de la latencia de los hosts monitoreados a lo largo del tiempo.")
    
    history_data = load_history()
    if history_data:
        df_hist = pd.DataFrame(history_data)
        # Convertir timestamp a datetime para graficar
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
        
        # Graficar con Streamlit
        st.line_chart(
            df_hist, 
            x="timestamp", 
            y="latencia", 
            color="ip",
            use_container_width=True
        )
        st.dataframe(df_hist.tail(20), use_container_width=True) # Mostrar últimos 20
    else:
        st.info("No hay datos de historial aún. Ejecuta un diagnóstico en la primera pestaña para empezar a recolectar datos.")