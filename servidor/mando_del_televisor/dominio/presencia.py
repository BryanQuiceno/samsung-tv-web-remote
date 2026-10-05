"""La presencia en red a lo largo del tiempo: el corazon de este sistema.

POR QUE ESTO EXISTE
-------------------
El UE40NU7115 no publica si su pantalla esta encendida, y APAGADO sigue
respondiendo por red a rachas. Medido el 2026-09-02 sobre el aparato real:

  - encendido : responde SIEMPRE, sin un solo hueco.
  - apagado   : responde ~90 s despues del apagado y vuelve a responder si algo
                lo estimula, pero NUNCA aguanta mas de ~2 min seguidos.

Ninguna consulta suelta (REST, SOAP, DLNA, SSDP, el canal del mando) distingue
los dos casos: todas contestan igual. Lo unico que un televisor apagado no puede
fingir es la CONSTANCIA. Por eso aqui no se pregunta "¿respondes?", se mide
"¿cuanto llevas respondiendo?".
"""
from dataclasses import dataclass

#: Lo mas que aguanta un televisor apagado con la red viva (medido: ~120 s).
AGUANTE_MAXIMO_APAGADA = 120.0

#: A partir de aqui la racha ya no puede venir de un televisor apagado.
#: Se deja margen sobre el aguante maximo para no decidir en el filo.
RACHA_PARA_FIARSE = 180.0

#: Si el vigia dejo de anotar mas de esto, la racha deja de ser creible:
#: pudo apagarse y encenderse sin que nadie lo viera.
HUECO_QUE_INVALIDA = 180.0


@dataclass(frozen=True)
class Muestra:
    """Una lectura suelta: en tal momento, respondia o no."""

    momento: float
    responde: bool


@dataclass(frozen=True)
class Racha:
    """Cuanto lleva el televisor en su situacion actual.

    `confirmada` la pone un encendido que ya se verifico aguantando en red: sirve
    para no volver a pedir tres minutos de espera a quien pregunta el estado
    justo despues de encender.
    """

    responde: bool
    desde: float
    ultima_muestra: float
    confirmada: bool = False

    def duracion(self, ahora: float) -> float:
        return ahora - self.desde

    def esta_fresca(self, ahora: float) -> bool:
        return ahora - self.ultima_muestra <= HUECO_QUE_INVALIDA

    def demuestra_que_esta_encendida(self, ahora: float) -> bool:
        if not self.responde or not self.esta_fresca(ahora):
            return False
        return self.confirmada or self.duracion(ahora) >= RACHA_PARA_FIARSE
