"""Caso de uso: pulsar una tecla del mando, como quien apunta con el de verdad."""
from ..dominio.puertos import CanalDeMando, SondaDeRed
from ..dominio.televisor import Tecla


class TelevisorDormido(Exception):
    def __init__(self) -> None:
        super().__init__("El televisor esta apagado: no recibe teclas")


class PulsarUnaTecla:
    def __init__(self, mando: CanalDeMando, sonda: SondaDeRed) -> None:
        self._mando = mando
        self._sonda = sonda

    def __call__(self, tecla: Tecla) -> None:
        if not self._sonda.mirar().despierto:
            raise TelevisorDormido()
        self._mando.pulsar(tecla)
