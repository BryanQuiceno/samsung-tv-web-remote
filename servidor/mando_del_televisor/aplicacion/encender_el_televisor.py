"""Caso de uso: encender, y no decir que esta encendida hasta comprobarlo.

Son dos cosas distintas y hay que hacer las dos:
  1. despertar la TARJETA DE RED  -> Wake-on-LAN
  2. levantar la PANTALLA         -> tecla de encendido por el canal del mando

El paso 2 se pierde a veces (el televisor esta a medio despertar y se come la
tecla). Ese era el "a veces no enciende" de siempre. Por eso despues se CONFIRMA
y, si no cuajo, se repite la secuencia entera una vez mas.
"""
from dataclasses import dataclass
from typing import Callable

from ..dominio.puertos import (
    Altavoces,
    CanalDeMando,
    DespertadorDeRed,
    HistorialDePresencia,
    Reloj,
    SondaDeRed,
)
from ..dominio.televisor import Estado, Tecla
from .avisos import Aviso, en_silencio
from .confirmar_el_estado import ConfirmarElEstado

ESPERA_MAXIMA_DE_RED = 90.0
ENTRE_INTENTOS = 3.0
CADA_CUANTOS_INTENTOS_SE_REPITE_EL_WAKE_ON_LAN = 3
CADA_CUANTOS_INTENTOS_SE_LE_BUSCA_EN_OTRA_DIRECCION = 3
INTENTOS_DE_TECLA = 2
RONDAS = 2


@dataclass(frozen=True)
class Encendido:
    encendida: bool
    mensaje: str


class EncenderElTelevisor:
    def __init__(
        self,
        despertador: DespertadorDeRed,
        sonda: SondaDeRed,
        mando: CanalDeMando,
        altavoces: Altavoces,
        historial: HistorialDePresencia,
        reloj: Reloj,
        confirmar: ConfirmarElEstado,
        reubicar: Callable[[], object] | None = None,
    ) -> None:
        self._despertador = despertador
        self._sonda = sonda
        self._mando = mando
        self._altavoces = altavoces
        self._historial = historial
        self._reloj = reloj
        self._confirmar = confirmar
        self._reubicar = reubicar

    def __call__(self, avisar: Aviso = en_silencio) -> Encendido:
        for ronda in range(1, RONDAS + 1):
            if not self._despertar_la_red(avisar, ronda):
                return Encendido(False, "No contesta al Wake-on-LAN. ¿Sigue enchufada a la red?")

            self._pulsar_encender()
            avisar("Tecla de encendido enviada. Comprobando que se queda encendida", 0.35)

            if self._confirmar(avisar) is Estado.ENCENDIDA:
                return Encendido(True, self._quitar_el_silencio())

            avisar("Se apago sola: la tecla se perdio. Lo intento otra vez", 0.0)

        return Encendido(False, "Se cayo de la red tras la tecla dos veces. No se quedo encendida.")

    def _despertar_la_red(self, avisar: Aviso, ronda: int) -> bool:
        de = "" if ronda == 1 else " (segundo intento)"
        avisar(f"Despertando el televisor{de}", 0.1)
        fin = self._reloj.ahora() + ESPERA_MAXIMA_DE_RED
        intento = 0
        while self._reloj.ahora() < fin:
            if intento % CADA_CUANTOS_INTENTOS_SE_REPITE_EL_WAKE_ON_LAN == 0:
                self._despertador.despertar()
            if self._sonda.responde():
                return True
            intento += 1
            # El Wake-on-LAN va a la MAC y despierta aunque el televisor haya
            # cambiado de direccion; pero entonces contesta en OTRA. Si no
            # aparece donde se le esperaba, se le busca antes de rendirse.
            if self._reubicar and intento % CADA_CUANTOS_INTENTOS_SE_LE_BUSCA_EN_OTRA_DIRECCION == 0:
                try:
                    self._reubicar()
                except Exception:
                    pass
            self._reloj.esperar(ENTRE_INTENTOS)
        return False

    def _pulsar_encender(self) -> None:
        for _ in range(INTENTOS_DE_TECLA):
            try:
                self._mando.pulsar(Tecla.ENCENDER)
                return
            except Exception:
                self._reloj.esperar(1)

    def _quitar_el_silencio(self) -> str:
        """Este televisor vuelve SIEMPRE silenciado. Si se pide encender es para oirla.

        Una sola orden, nunca un bucle: cada orden de audio dibuja el icono de
        silencio en la pantalla y encadenarlas se ve como un parpadeo absurdo.
        """
        fin = self._reloj.ahora() + 20
        while self._reloj.ahora() < fin:
            if self._altavoces.estan_disponibles():
                try:
                    self._altavoces.silenciar(False)
                    # Quitar el silencio no garantiza que se oiga: si el volumen
                    # quedo a cero, decir "con sonido" seria mentir igual.
                    if self._altavoces.leer().volumen == 0:
                        return "Encendida, pero el volumen esta a cero"
                    return "Encendida y con sonido"
                except Exception:
                    break
            self._reloj.esperar(2)
        return "Encendida (no me dio tiempo a quitarle el silencio)"
