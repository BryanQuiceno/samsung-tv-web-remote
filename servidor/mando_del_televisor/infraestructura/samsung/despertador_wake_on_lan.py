"""Wake-on-LAN: el sobre magico que despierta la tarjeta de red del televisor.

🚨 El socket se ATA a la IP de la red de casa. Este servidor tiene varias
interfaces (docker0, br-*, tailscale0) y un mensaje de difusion sin atar se iba
por la que no era: el televisor no lo recibia y el encendido fallaba a ratos.
Con la atadura acierta a la primera (medido: encendido en 4 s).

Cual es esa IP se pregunta al sistema en cada encendido (`red`), no se escribe a
mano: asi un cambio de direccion del servidor no rompe el encendido.

El sobre va dirigido a la MAC, no a la direccion del televisor: por eso
despierta aunque el televisor haya cambiado de direccion.
"""
import socket
from typing import Callable

from ..red.red_de_casa import RedDeCasa

CABECERA = b"\xff" * 6
REPETICIONES_DE_LA_MAC = 16
PUERTOS = (9, 7)


class DespertadorWakeOnLan:
    def __init__(self, mac: str, red: Callable[[], RedDeCasa]) -> None:
        self._sobre = CABECERA + bytes.fromhex(mac.replace(":", "").replace("-", "")) * REPETICIONES_DE_LA_MAC
        self._red = red

    def despertar(self) -> None:
        red = self._red()
        destinos = dict.fromkeys((red.difusion, "255.255.255.255"))
        for puerto in PUERTOS:
            enchufe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            enchufe.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            try:
                if red.ip:
                    enchufe.bind((red.ip, 0))
            except OSError:
                pass          # sin atadura sigue valiendo; solo es menos fiable
            for destino in destinos:
                try:
                    enchufe.sendto(self._sobre, (destino, puerto))
                except OSError:
                    pass
            enchufe.close()
