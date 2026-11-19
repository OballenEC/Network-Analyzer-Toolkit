# src/device_manager.py
import time
from netmiko import ConnectHandler

def get_device_info_ssh(ip: str, username: str, password: str, device_type: str = "cisco_ios"):
    """Obtiene el 'show version' y vecinos LLDP/CDP vía SSH."""
    device = {
        "device_type": device_type,
        "host": ip,
        "username": username,
        "password": password,
        "timeout": 5,
    }
    try:
        with ConnectHandler(**device) as net_connect:
            version = net_connect.send_command("show version")
            neighbors = net_connect.send_command("show lldp neighbors")
            return {"status": "success", "version": version, "neighbors": neighbors}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_snmp_metrics(ip: str, community: str = 'public'):
    """
    Consulta SNMPv2c usando la API async de PySNMP 7.x.
    Devuelve dict con sysName, sysUpTime, ifNumber o {'status': 'error', 'message': ...}.
    """
    async def _query():
        try:
            transport = await UdpTransportTarget.create((ip, 161), timeout=2, retries=1)
            errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
                SnmpEngine(),
                CommunityData(community, mpModel=1),  # mpModel=1 → SNMPv2c
                transport,
                ContextData(),
                ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0)),
                ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysUpTime', 0)),
                ObjectType(ObjectIdentity('IF-MIB', 'ifNumber', 0)),
            )
            if errorIndication:
                return {'status': 'error', 'message': str(errorIndication)}
            if errorStatus:
                return {'status': 'error', 'message': errorStatus.prettyPrint()}
            return {
                'status': 'success',
                'sysName': str(varBinds[0][1]),
                'sysUpTime': str(varBinds[1][1]),
                'ifNumber': str(varBinds[2][1]),
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    try:
        return asyncio.run(_query())
    except Exception as e:
        return {'status': 'error', 'message': f'Error en SNMP: {e}'}
