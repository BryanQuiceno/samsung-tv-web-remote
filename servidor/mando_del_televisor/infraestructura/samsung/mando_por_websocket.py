"""El canal de teclas: WebSocket seguro contra el puerto 8002 del televisor.

Necesita un token de emparejamiento, que se obtiene una unica vez con alguien
delante del televisor aceptando el aviso con el mando de verdad.
"""
import os
from typing import Callable

from ...dominio.televisor import Tecla


ESPERA_A_QUE_ACEPTEN = 45


class MandoPorWebSocket:
    PUERTO = 8002

    def __init__(self, donde: Callable[[], str], fichero_de_token: str, nombre: str = "MandoCasa", espera: float = 10.0) -> None:
        self._donde = donde
        self._token = fichero_de_token
        self._nombre = nombre
        self._espera = espera

    def _abrir(self, espera: float | None = None):
        from samsungtvws import SamsungTVWS

        return SamsungTVWS(
            host=self._donde(),
            port=self.PUERTO,
            token_file=self._token,
            name=self._nombre,
            timeout=espera or self._espera,
        )

    def pulsar(self, tecla: Tecla) -> None:
        self._abrir().send_key(tecla.value)

    def emparejar(self) -> bool:
        """Pide el emparejamiento. Alguien tiene que aceptarlo EN la pantalla.

        Basta con abrir el canal: el televisor saca el aviso, y al aceptarlo
        devuelve el token, que queda guardado. No se pulsa ninguna tecla.
        """
        canal = self._abrir(espera=ESPERA_A_QUE_ACEPTEN)
        try:
            canal.open()
        except Exception:
            return False          # dijeron que no, o nadie contesto a tiempo
        finally:
            try:
                canal.close()
            except Exception:
                pass
        return self.esta_emparejado()

    def esta_emparejado(self) -> bool:
        try:
            return os.path.getsize(self._token) > 0
        except OSError:
            return False
