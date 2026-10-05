"""Casos de uso del sonido: volumen y silencio.

El televisor solo atiende el audio despierto, asi que estos casos de uso fallan
a proposito con un mensaje claro en vez de fingir que hicieron algo.
"""
from ..dominio.puertos import Altavoces
from ..dominio.televisor import Sonido

VOLUMEN_MINIMO = 0
VOLUMEN_MAXIMO = 100


class TelevisorDormido(Exception):
    """Se pidio tocar el sonido con el televisor sin despertar."""

    def __init__(self) -> None:
        super().__init__("El televisor esta apagado: enciendelo para tocar el sonido")


class AjustarElVolumen:
    def __init__(self, altavoces: Altavoces) -> None:
        self._altavoces = altavoces

    def a(self, volumen: int) -> Sonido:
        return self._poner(volumen)

    def subir(self, paso: int = 1) -> Sonido:
        return self._poner(self._leer().volumen + paso)

    def bajar(self, paso: int = 1) -> Sonido:
        return self._poner(self._leer().volumen - paso)

    def _poner(self, volumen: int) -> Sonido:
        acotado = max(VOLUMEN_MINIMO, min(VOLUMEN_MAXIMO, int(volumen)))
        try:
            self._altavoces.poner_volumen(acotado)
            return self._altavoces.leer()
        except Exception as error:
            raise TelevisorDormido() from error

    def _leer(self) -> Sonido:
        try:
            return self._altavoces.leer()
        except Exception as error:
            raise TelevisorDormido() from error


class SilenciarElTelevisor:
    def __init__(self, altavoces: Altavoces) -> None:
        self._altavoces = altavoces

    def __call__(self, silenciado: bool | None = None) -> Sonido:
        try:
            actual = self._altavoces.leer()
            self._altavoces.silenciar(not actual.silenciado if silenciado is None else silenciado)
            return self._altavoces.leer()
        except Exception as error:
            raise TelevisorDormido() from error
