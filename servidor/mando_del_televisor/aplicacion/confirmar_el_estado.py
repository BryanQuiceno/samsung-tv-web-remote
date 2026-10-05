"""Caso de uso: deshacer una duda esperando.

Cuando el estado sale DUDOSA solo cabe una cosa honesta: mirar un rato. Un
televisor apagado se cae de la red en menos de dos minutos; uno encendido no se
cae nunca. Se vigila hasta `AGUANTE_MAXIMO_APAGADA` con margen y se responde.

Solo se hacen consultas de red, que estan comprobadas que NO despiertan a un
televisor apagado (a diferencia de abrir el canal del mando, que si lo hace).
"""
from ..dominio.presencia import AGUANTE_MAXIMO_APAGADA
from ..dominio.puertos import HistorialDePresencia, Reloj, SondaDeRed
from ..dominio.televisor import Estado
from .avisos import Aviso, en_silencio

MARGEN = 10.0
ENTRE_MIRADAS = 10.0
#: Un televisor que dice su estado tarda unos segundos en pasar a "encendido".
ESPERA_A_QUE_LO_DIGA = 25.0
ENTRE_PREGUNTAS = 2.0


class ConfirmarElEstado:
    def __init__(self, sonda: SondaDeRed, historial: HistorialDePresencia, reloj: Reloj) -> None:
        self._sonda = sonda
        self._historial = historial
        self._reloj = reloj

    def __call__(self, avisar: Aviso = en_silencio) -> Estado:
        if self._sonda.mirar().pantalla is not None:
            return self._preguntarselo(avisar)

        vigilancia = AGUANTE_MAXIMO_APAGADA + MARGEN
        fin = self._reloj.ahora() + vigilancia

        while self._reloj.ahora() < fin:
            self._reloj.esperar(ENTRE_MIRADAS)
            responde = self._sonda.responde()
            self._historial.anotar(responde)
            if not responde:
                avisar("Se ha caido de la red: estaba apagada", 1.0)
                return Estado.APAGADA
            restante = max(0.0, fin - self._reloj.ahora())
            avisar(
                f"Aguantando en red, {int(restante)} s para confirmarlo",
                1 - restante / vigilancia,
            )

        self._historial.dar_por_confirmada()
        avisar("Confirmado: la pantalla esta encendida", 1.0)
        return Estado.ENCENDIDA

    def _preguntarselo(self, avisar: Aviso) -> Estado:
        """Para los televisores que dicen su estado: basta con preguntar un rato."""
        fin = self._reloj.ahora() + ESPERA_A_QUE_LO_DIGA
        while True:
            encendida = bool(self._sonda.mirar().pantalla)
            self._historial.anotar(encendida)
            if encendida:
                self._historial.dar_por_confirmada()
                avisar("Confirmado: la pantalla esta encendida", 1.0)
                return Estado.ENCENDIDA
            if self._reloj.ahora() >= fin:
                avisar("El televisor dice que sigue apagado", 1.0)
                return Estado.APAGADA
            self._reloj.esperar(ENTRE_PREGUNTAS)
