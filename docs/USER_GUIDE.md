# Guía de usuario — Network Diagnostic Toolkit (NDT)

## Primer inicio

Al abrir la aplicación, verás el **Manual de bienvenida**. Debes pulsar **✅ Acepto y comienzo** para acceder. Si cierras el diálogo con la X, verás un mensaje explicando por qué no se accedió.

## Pestaña 1: Diagnóstico de red

### Ejecutar diagnóstico
1. En **TARGET ACQUISITION**, introduce IPs, dominios o rangos CIDR.
2. Pulsa **▶ EJECUTAR DIAGNÓSTICO**.
3. Revisa:
   - **TELEMETRÍA:** total, disponibles, no disponibles, disponibilidad, latencia promedio.
   - **LECTURA Y CONCLUSIONES:** interpretación automática.
   - **DATOS DE RED:** tabla con IP, estado, latencia, clasificación.
   - **TOPOLOGÍA INTERACTIVA:** grafo con hosts y conexiones.
   - **EXPORTAR:** CSV o \.pkt\.

### Traceroute
1. Introduce un destino en **TARGET ACQUISITION**.
2. Pulsa **🌐 TRAZADO DE RUTA**.
3. Revisa los saltos y la lectura interpretativa.

## Pestaña 2: NetDevOps

### SSH
1. Introduce IP, usuario y contraseña.
2. Pulsa **🔌 Probar SSH**.
3. Revisa \show version\ y vecinos LLDP.

### SNMP
1. Introduce IP y community.
2. Pulsa **📶 Probar SNMP**.
3. Revisa \sysName\, \sysUpTime\, \ifNumber\.

## Pestaña 3: Historial

- Muestra la evolución de latencias de los hosts monitoreados.
- Requiere haber ejecutado diagnósticos previos.

## Modo Demo

Selecciona **🟢 Demo (simulado)** en el sidebar para probar la interfaz sin enviar tráfico real.

## Limitaciones

- El escaneo de puertos debe usarse solo en redes controladas.
- SNMPv1/v2c envía la community en texto plano.