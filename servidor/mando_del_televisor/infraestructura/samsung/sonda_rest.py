"""¿Contesta el televisor? Se pregunta por su ficha REST del puerto 8001.

Se eligio esta y no otra a proposito: es una consulta pasiva. Abrir el canal del
mando (WebSocket 8002) TAMBIEN contesta, pero ademas despierta a un televisor
apagado, y entonces la medicion de presencia se estaria falseando a si misma.
"""
import json
import urllib.request
from typing import Callable

from ...dominio.televisor import Vistazo


class SondaRest:
    PUERTO = 8001

    def __init__(self, donde: Callable[[], str], espera: float = 3.0) -> None:
        # `donde` se pregunta en cada consulta: la direccion puede cambiar con
        # el programa en marcha (ver dominio/direccion.py).
        self._donde = donde
        self._espera = espera

    def responde(self) -> bool:
        return self.ficha() is not None

    def mirar(self) -> Vistazo:
        ficha = self.ficha()
        if ficha is None:
            return Vistazo(en_red=False)
        # Los modelos modernos traen `PowerState` ("on" / "standby"); el
        # UE40NU7115 no lo trae y por eso `pantalla` se queda en None.
        dicho = (ficha.get("device") or {}).get("PowerState")
        return Vistazo(en_red=True, pantalla=None if dicho is None else str(dicho).lower() == "on")

    def ficha(self) -> dict | None:
        try:
            with urllib.request.urlopen(f"http://{self._donde()}:{self.PUERTO}/api/v2/", timeout=self._espera) as respuesta:
                return json.loads(respuesta.read().decode())
        except Exception:
            return None
