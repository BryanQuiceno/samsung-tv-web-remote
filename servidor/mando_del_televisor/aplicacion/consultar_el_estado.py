"""Caso de uso: ¿como esta el televisor?

Regla (ver dominio/presencia.py para las mediciones que la sostienen):
    no responde                  -> APAGADA   (certeza inmediata)
    responde de forma sostenida  -> ENCENDIDA (certeza)
    responde pero acaba de       -> DUDOSA    (aun no se puede afirmar;
    despertar                                  `ConfirmarElEstado` lo resuelve)

Eso es para los televisores que NO dicen si estan encendidos (el UE40NU7115).
Los modernos lo dicen ellos mismos y entonces no hay nada que deducir: se les
cree, y nunca salen DUDOSA.
"""
from dataclasses import dataclass

from ..dominio.presencia import Racha
from ..dominio.puertos import Altavoces, HistorialDePresencia, Reloj, SondaDeRed
from ..dominio.televisor import Estado, Sonido


@dataclass(frozen=True)
class Situacion:
    estado: Estado
    sonido: Sonido | None          # solo se puede leer con el televisor despierto
    racha: Racha | None
    segundos_en_este_estado: float


class ConsultarElEstado:
    def __init__(
        self,
        sonda: SondaDeRed,
        historial: HistorialDePresencia,
        altavoces: Altavoces,
        reloj: Reloj,
    ) -> None:
        self._sonda = sonda
        self._historial = historial
        self._altavoces = altavoces
        self._reloj = reloj

    def __call__(self, con_sonido: bool = True) -> Situacion:
        vistazo = self._sonda.mirar()
        responde = vistazo.despierto
        racha = self._historial.anotar(responde)
        ahora = self._reloj.ahora()

        if not responde:
            estado = Estado.APAGADA
        elif vistazo.pantalla or racha.demuestra_que_esta_encendida(ahora):
            estado = Estado.ENCENDIDA
        else:
            estado = Estado.DUDOSA

        sonido = None
        if con_sonido and responde:
            try:
                sonido = self._altavoces.leer()
            except Exception:
                sonido = None      # el audio duerme antes que el resto: no es un fallo

        return Situacion(estado, sonido, racha, racha.duracion(ahora))
