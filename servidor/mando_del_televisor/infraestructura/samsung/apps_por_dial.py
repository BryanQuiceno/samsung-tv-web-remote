"""Abrir aplicaciones del televisor por DIAL (el mismo mecanismo que usa el
boton de "enviar a la tele" del movil).

Por que DIAL y no navegar a ciegas por los menus: DIAL permite decirle a Netflix
QUE ver, no solo que se abra. Se manda el identificador del titulo y la
aplicacion arranca ya dentro de el. Navegar con flechas seria adivinar donde
esta el cursor, y falla en cuanto Netflix cambia su pantalla de inicio.

Especificacion: http://www.dial-multiscreen.org/ (dialVer 2.1 en este televisor).
"""
import urllib.request
from typing import Callable

PUERTO = 8080


class AppsPorDial:
    def __init__(self, donde: Callable[[], str], espera: float = 10.0) -> None:
        self._donde = donde
        self._espera = espera

    @property
    def _base(self) -> str:
        return f"http://{self._donde()}:{PUERTO}/ws/app"

    def lanzar(self, app: str, contenido: str | None = None) -> None:
        # Netflix espera "v=<identificador del titulo>" como cuerpo de la peticion.
        cuerpo = f"v={contenido}".encode() if contenido else b""
        peticion = urllib.request.Request(
            f"{self._base}/{app}",
            data=cuerpo,
            headers={"Content-Type": "text/plain; charset=utf-8"},
            method="POST",
        )
        urllib.request.urlopen(peticion, timeout=self._espera).read()

    def esta_abierta(self, app: str) -> bool:
        try:
            with urllib.request.urlopen(f"{self._base}/{app}", timeout=self._espera) as r:
                return "<state>running</state>" in r.read().decode()
        except Exception:
            return False
