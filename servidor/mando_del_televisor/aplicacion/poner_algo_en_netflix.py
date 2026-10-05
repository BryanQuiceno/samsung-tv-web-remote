"""Caso de uso: poner algo concreto en Netflix, sin navegar por menus.

Un titulo de Netflix se identifica por el numero que sale en su direccion web:
    https://www.netflix.com/es/title/80026226  ->  80026226
Se acepta la direccion entera o solo el numero, porque el numero suelto no hay
quien lo recuerde.
"""
import re
from typing import Callable

from ..dominio.puertos import LanzadorDeApps, SondaDeRed

APP = "Netflix"

#: Los titulos que se piden por su nombre los pone cada casa (ver
#: `datos/netflix.json`); aqui no hay ninguno escrito.
SinTitulos: Callable[[], dict[str, str]] = dict


class TelevisorDormido(Exception):
    def __init__(self) -> None:
        super().__init__("El televisor esta apagado: enciendelo antes de poner nada")


class PonerAlgoEnNetflix:
    def __init__(
        self,
        lanzador: LanzadorDeApps,
        sonda: SondaDeRed,
        conocidos: Callable[[], dict[str, str]] = SinTitulos,
    ) -> None:
        self._lanzador = lanzador
        self._sonda = sonda
        self._conocidos = conocidos

    def __call__(self, titulo: str | None = None) -> str:
        if not self._sonda.mirar().despierto:
            raise TelevisorDormido()
        identificador = self._identificar(titulo) if titulo else None
        self._lanzador.lanzar(APP, identificador)
        return f"Netflix abierto en el titulo {identificador}" if identificador else "Netflix abierto"

    def _identificar(self, titulo: str) -> str:
        limpio = titulo.strip().lower()
        conocidos = {nombre.strip().lower(): str(numero) for nombre, numero in self._conocidos().items()}
        if limpio in conocidos:
            return conocidos[limpio]
        numeros = re.findall(r"\d{6,}", limpio)   # vale la direccion entera o el numero
        if numeros:
            return numeros[-1]
        de_la_casa = f", o uno de estos: {', '.join(sorted(conocidos))}" if conocidos else ""
        raise ValueError(f"No se que es «{titulo}». Pasa el enlace de Netflix del titulo{de_la_casa}")
