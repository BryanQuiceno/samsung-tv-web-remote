"""Donde vive el televisor en la red, y por que creemos que es ahi.

La direccion (IP) la reparte el router y PUEDE CAMBIAR: basta con que el router
se reinicie o caduque el prestamo. Lo que no cambia nunca es la MAC, que viene
grabada en la tarjeta de red. Por eso la MAC es la identidad del aparato y la
direccion es solo "donde esta hoy".

Medido el 2026-10-05: el televisor paso de .146 a .128 el 16 de septiembre y el
mando estuvo 19 dias llamando a una direccion vacia, diciendo "apagada".
"""
import ipaddress
from dataclasses import dataclass
from enum import Enum


#: La de un televisor que aun no tiene ninguna apuntada. No es de nadie.
SIN_DIRECCION = "0.0.0.0"


class Origen(str, Enum):
    """Quien puso la direccion que estamos usando."""

    DE_FABRICA = "de_fabrica"    # aun no se sabe: nunca se ha apuntado ninguna
    AL_ANADIRLO = "al_anadirlo"  # la que tenia el dia que se añadio al mando
    A_MANO = "a_mano"            # alguien la escribio en los ajustes
    ENCONTRADA = "encontrada"    # el mando la encontro solo, por la MAC


@dataclass(frozen=True)
class Direccion:
    ip: str
    origen: Origen = Origen.DE_FABRICA
    desde: float | None = None       # cuando se empezo a usar
    anterior: str | None = None      # la que habia antes, para poder contarlo


class DireccionNoValida(ValueError):
    """Lo escrito no es una direccion de red de casa."""


class EsOtroAparato(ValueError):
    """En esa direccion contesta algo que no es el televisor."""


def direccion_valida(texto: str) -> str:
    """Devuelve la direccion limpia, o explica por que no vale."""
    limpio = (texto or "").strip()
    try:
        ip = ipaddress.IPv4Address(limpio)
    except ValueError:
        raise DireccionNoValida(f"«{limpio}» no es una dirección. Tiene que ser como 192.168.1.50")
    if not ip.is_private or ip.is_loopback or ip.is_link_local:
        raise DireccionNoValida(f"{ip} no es una dirección de la red de casa")
    return str(ip)


def misma_mac(una: str | None, otra: str | None) -> bool:
    limpia = lambda m: (m or "").lower().replace("-", ":").strip()
    return bool(una) and limpia(una) == limpia(otra)
