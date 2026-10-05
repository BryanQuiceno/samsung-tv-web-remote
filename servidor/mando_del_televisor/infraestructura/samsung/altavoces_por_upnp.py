"""Volumen y silencio por UPnP (RenderingControl) en el puerto 9197.

Es el mismo protocolo que usan los equipos de musica de red. Solo contesta con
el televisor despierto, y ademas tarda unos segundos mas que el resto en
levantarse tras un encendido.
"""
import socket
import urllib.request
from typing import Callable

from ...dominio.televisor import Sonido

SOBRE = (
    '<?xml version="1.0"?>'
    '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
    's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
    '<u:{accion} xmlns:u="urn:schemas-upnp-org:service:RenderingControl:1">'
    "<InstanceID>0</InstanceID><Channel>Master</Channel>{extra}"
    "</u:{accion}></s:Body></s:Envelope>"
)


def _entre_etiquetas(xml: str, etiqueta: str) -> str | None:
    inicio = xml.find(f"<{etiqueta}>")
    if inicio < 0:
        return None
    return xml[inicio + len(etiqueta) + 2 : xml.find(f"</{etiqueta}>", inicio)]


class AltavocesPorUpnp:
    PUERTO = 9197

    def __init__(self, donde: Callable[[], str], espera: float = 4.0) -> None:
        self._donde = donde
        self._espera = espera

    def _pedir(self, accion: str, extra: str = "") -> str:
        cuerpo = SOBRE.format(accion=accion, extra=extra).encode()
        peticion = urllib.request.Request(
            f"http://{self._donde()}:{self.PUERTO}/upnp/control/RenderingControl1",
            data=cuerpo,
            headers={
                "Content-Type": 'text/xml; charset="utf-8"',
                "SOAPACTION": f'"urn:schemas-upnp-org:service:RenderingControl:1#{accion}"',
            },
        )
        with urllib.request.urlopen(peticion, timeout=self._espera) as respuesta:
            return respuesta.read().decode()

    def leer(self) -> Sonido:
        volumen = int(_entre_etiquetas(self._pedir("GetVolume"), "CurrentVolume"))
        silenciado = _entre_etiquetas(self._pedir("GetMute"), "CurrentMute") in ("1", "true")
        return Sonido(volumen=volumen, silenciado=silenciado)

    def poner_volumen(self, volumen: int) -> None:
        self._pedir("SetVolume", f"<DesiredVolume>{volumen}</DesiredVolume>")

    def silenciar(self, silenciado: bool) -> None:
        self._pedir("SetMute", f"<DesiredMute>{1 if silenciado else 0}</DesiredMute>")

    def estan_disponibles(self) -> bool:
        enchufe = socket.socket()
        enchufe.settimeout(2)
        try:
            enchufe.connect((self._donde(), self.PUERTO))
            return True
        except OSError:
            return False
        finally:
            enchufe.close()
