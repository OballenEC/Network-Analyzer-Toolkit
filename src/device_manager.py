# src/device_manager.py
import time
from netmiko import ConnectHandler
from pysnmp.hlapi import *

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

def get_snmp_metrics(ip: str, community: str = "public"):
    """Consulta el nombre del dispositivo (sysName) vía SNMP (Capa 4)."""
    try:
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip, 161), timeout=2, retries=0),
            ContextData(),
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0))
        )
        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
        
        if errorIndication:
            return {"status": "error", "message": str(errorIndication)}
        elif errorStatus:
            return {"status": "error", "message": errorStatus.prettyPrint()}
        else:
            for varBind in varBinds:
                return {"status": "success", "sysName": varBind[1].prettyPrint()}
    except Exception as e:
        return {"status": "error", "message": str(e)}