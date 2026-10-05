"""Caso de uso: apagar.

Al apagar hay que ROMPER la racha de presencia a proposito: la red del televisor
sigue viva ~90 s despues, y sin esto quien pregunte el estado en ese rato veria
una racha larga y responderia "encendida" recien apagada.
"""
from dataclasses import dataclass

from ..dominio.puertos import CanalDeMando, HistorialDePresencia, SondaDeRed
from ..dominio.televisor import Tecla


@dataclass(frozen=True)
class Apagado:
    ya_estaba_apagada: bool
    mensaje: str


class ApagarElTelevisor:
    def __init__(self, mando: CanalDeMando, sonda: SondaDeRed, historial: HistorialDePresencia) -> None:
        self._mando = mando
        self._sonda = sonda
        self._historial = historial

    def __call__(self) -> Apagado:
        if not self._sonda.mirar().despierto:
            return Apagado(True, "Ya estaba apagada")
        self._mando.pulsar(Tecla.APAGAR)
        self._historial.romper()
        return Apagado(False, "Apagada")
