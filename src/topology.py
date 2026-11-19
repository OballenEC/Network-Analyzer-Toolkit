from pyvis.network import Network
import streamlit.components.v1 as components

def render_topology(results):
    # Crear red con fondo oscuro
    net = Network(height="450px", width="100%", bgcolor="#0a0e14", font_color="#00ff41", directed=False)
    
    # Física de los nodos (efecto muelle)
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=150)

    # Nodo central
    net.add_node(1, label="TU PC (Scanner)", color="#ffffff", shape="star", size=30)

    for i, r in enumerate(results):
        node_id = i + 2
        if r.estado == "no_disponible":
            color = "#ff0040"
            label = f"{r.ip}\nTIMEOUT"
        elif r.lento:
            color = "#ffb000"
            label = f"{r.ip}\n{r.latencia_promedio_ms} ms"
        else:
            color = "#00ff41"
            label = f"{r.ip}\n{r.latencia_promedio_ms} ms"

        # Agregar nodo y línea de conexión al nodo central
        net.add_node(node_id, label=label, color=color, shape="box")
        net.add_edge(1, node_id, color="#8b949e", width=2)

    # Generar el HTML interactivo y renderizarlo
    html = net.generate_html()
    components.html(html, height=450)