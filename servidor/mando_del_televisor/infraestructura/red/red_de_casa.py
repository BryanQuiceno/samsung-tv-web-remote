"""Por donde sale este servidor a la red de casa.

Se pregunta al sistema en vez de escribirlo a mano: si el servidor cambia de
direccion, o la casa entera cambia de numeracion, esto se entera solo.

Hace falta saberlo por dos motivos: el Wake-on-LAN tiene que salir por la
tarjeta de casa y no por las de Docker o Tailscale (ver
despertador_wake_on_lan.py), y para buscar el televisor hay que saber que
direcciones existen en casa.
"""
import ipaddress
import json
import subprocess
from dataclasses import dataclass

MAYOR_RED_QUE_SE_RECORRE = 1024      # mas alla de esto no es una casa


@dataclass(frozen=True)
class RedDeCasa:
    ip: str | None            # la direccion de este servidor en casa
    difusion: str             # a donde se grita para que lo oigan todos
    interfaz: str | None
    direcciones: tuple[str, ...] = ()


SIN_RED = RedDeCasa(ip=None, difusion="255.255.255.255", interfaz=None)


def _ip(*argumentos: str) -> list[dict]:
    salida = subprocess.run(["ip", "-j", *argumentos], capture_output=True, text=True, timeout=5)
    return json.loads(salida.stdout or "[]")


#: Para preguntar "¿por donde sales a la calle?" cuando no hay un televisor
#: concreto en mente. No se le manda nada: solo se consulta la tabla de rutas.
UNA_DIRECCION_DE_FUERA = "1.1.1.1"


def red_de_casa(hacia: str | None = None) -> RedDeCasa:
    """La tarjeta por la que este servidor llegaria a la direccion `hacia`."""
    try:
        ruta = _ip("route", "get", hacia or UNA_DIRECCION_DE_FUERA)[0]
        interfaz = ruta["dev"]
        for tarjeta in _ip("-4", "addr", "show", "dev", interfaz):
            for dato in tarjeta.get("addr_info", []):
                red = ipaddress.ip_interface(f"{dato['local']}/{dato['prefixlen']}").network
                vecinas = ()
                if red.num_addresses <= MAYOR_RED_QUE_SE_RECORRE:
                    vecinas = tuple(str(d) for d in red.hosts() if str(d) != dato["local"])
                return RedDeCasa(
                    ip=dato["local"],
                    difusion=dato.get("broadcast") or str(red.broadcast_address),
                    interfaz=interfaz,
                    direcciones=vecinas,
                )
    except Exception:
        pass
    return SIN_RED
