"""Encontrar un aparato por su MAC, preguntando a la libreta de vecinos del sistema.

Todo ordenador apunta, para cada direccion con la que habla, la MAC que le
contesto (es la tabla ARP; se ve con `ip neigh`). Leerla es gratis y no molesta
a nadie. Si el aparato no esta apuntado, se llama a todas las puertas de la red
de casa: cada llamada obliga al sistema a preguntar «¿quien tiene esta
direccion?» y el que contesta queda apuntado con su MAC.

No hace falta ser administrador para nada de esto.

Una direccion apuntada puede estar caducada (el aparato se mudo y la linea
vieja sigue ahi un rato), asi que antes de darla por buena se comprueba con un
ping que sigue contestando ESA MAC.
"""
import json
import socket
import subprocess
import time
from typing import Callable

from ...dominio.direccion import misma_mac
from .red_de_casa import RedDeCasa

PUERTO_QUE_NO_ESCUCHA_NADIE = 9          # «discard»: el paquete se tira, solo importa la pregunta previa
ESPERA_A_QUE_CONTESTEN = 1.5
NO_VALEN = {"FAILED", "INCOMPLETE"}


class BuscadorPorVecinos:
    def __init__(self, red: Callable[[], RedDeCasa]) -> None:
        self._red = red

    def donde_esta(self, mac: str, a_fondo: bool = False) -> str | None:
        hallada = self._la_que_contesta(mac)
        if hallada or not a_fondo:
            return hallada
        self._llamar_a_todas_las_puertas()
        return self._la_que_contesta(mac)

    def quien_contesta_en(self, ip: str) -> str | None:
        if not self._ping(ip):
            return None
        for vecino in self._vecinos():
            if vecino["dst"] == ip and vecino.get("lladdr"):
                return vecino["lladdr"]
        return None

    # ---------------------------------------------------------------- privado
    def _la_que_contesta(self, mac: str) -> str | None:
        candidatas = [v["dst"] for v in self._vecinos() if misma_mac(v.get("lladdr"), mac)]
        for ip in candidatas:
            if misma_mac(self.quien_contesta_en(ip), mac):
                return ip
        return None

    def _vecinos(self) -> list[dict]:
        interfaz = self._red().interfaz
        orden = ["ip", "-j", "-4", "neigh", "show"] + (["dev", interfaz] if interfaz else [])
        try:
            salida = subprocess.run(orden, capture_output=True, text=True, timeout=5).stdout
            return [v for v in json.loads(salida or "[]") if not NO_VALEN & set(v.get("state", []))]
        except Exception:
            return []

    def _llamar_a_todas_las_puertas(self) -> None:
        red = self._red()
        enchufe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            if red.ip:
                enchufe.bind((red.ip, 0))
            for ip in red.direcciones:
                try:
                    enchufe.sendto(b"", (ip, PUERTO_QUE_NO_ESCUCHA_NADIE))
                except OSError:
                    pass
        except OSError:
            pass
        finally:
            enchufe.close()
        time.sleep(ESPERA_A_QUE_CONTESTEN)

    @staticmethod
    def _ping(ip: str) -> bool:
        try:
            return subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip], capture_output=True, timeout=4
            ).returncode == 0
        except Exception:
            return False
