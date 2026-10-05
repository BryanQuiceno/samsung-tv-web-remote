"""Encontrar televisores Samsung en la red de casa.

Todo Samsung con Tizen publica su ficha en el puerto 8001 sin pedir permiso:
nombre, modelo y si acepta el mando por red. Se llama a esa puerta en todas las
direcciones de casa a la vez y se apunta quien contesta. Es la misma consulta
pasiva que usa la sonda: no despierta ni molesta a nadie.

Solo salen los que estan en la red en ese momento. Un televisor apagado del todo
no contesta: por eso la web dice «enciendelo y vuelve a buscar».

La MAC se le pregunta a la libreta de vecinos del sistema y no a la ficha: la
ficha solo trae la del wifi, y un televisor por cable necesita la del cable para
que el Wake-on-LAN lo despierte.
"""
import json
import socket
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from ...dominio.puertos import BuscadorEnLaRed
from ...dominio.televisor import Hallazgo
from ..red.red_de_casa import RedDeCasa

PUERTO = 8001
ESPERA_A_QUE_ABRA = 0.6
ESPERA_A_LA_FICHA = 3.0
A_LA_VEZ = 64


class ExploradorSamsung:
    def __init__(self, red: Callable[[], RedDeCasa], buscador: BuscadorEnLaRed) -> None:
        self._red = red
        self._buscador = buscador

    def explorar(self) -> list[Hallazgo]:
        direcciones = self._red().direcciones
        if not direcciones:
            return []
        with ThreadPoolExecutor(A_LA_VEZ) as hilos:
            abiertas = [ip for ip, abre in zip(direcciones, hilos.map(self._abre_la_puerta, direcciones)) if abre]
            hallados = [h for h in hilos.map(self.mirar, abiertas) if h]
        return sorted(hallados, key=lambda h: h.nombre.lower())

    def mirar(self, ip: str) -> Hallazgo | None:
        try:
            with urllib.request.urlopen(f"http://{ip}:{PUERTO}/api/v2/", timeout=ESPERA_A_LA_FICHA) as respuesta:
                ficha = json.loads(respuesta.read().decode()).get("device") or {}
        except Exception:
            return None
        if "samsung" not in str(ficha.get("type", "")).lower():
            return None
        mac = self._buscador.quien_contesta_en(ip) or ficha.get("wifiMac") or ""
        return Hallazgo(
            ip=ip,
            mac=mac.upper(),
            nombre=_sin_etiqueta(ficha.get("name") or ficha.get("modelName") or "Televisor"),
            modelo=ficha.get("modelName") or ficha.get("model") or "Samsung",
            compatible=str(ficha.get("TokenAuthSupport", "")).lower() == "true" and bool(mac),
            dice_su_estado="PowerState" in ficha,
        )

    @staticmethod
    def _abre_la_puerta(ip: str) -> bool:
        enchufe = socket.socket()
        enchufe.settimeout(ESPERA_A_QUE_ABRA)
        try:
            enchufe.connect((ip, PUERTO))
            return True
        except OSError:
            return False
        finally:
            enchufe.close()


def _sin_etiqueta(nombre: str) -> str:
    """Samsung los llama «[TV] Salon»: la etiqueta sobra, ya se sabe que es una tele."""
    limpio = nombre.strip()
    if limpio.upper().startswith("[TV]"):
        limpio = limpio[4:].strip()
    return limpio or "Televisor"
