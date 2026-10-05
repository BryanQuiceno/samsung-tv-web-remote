"""El televisor y lo unico que de verdad se puede afirmar sobre el.

Este fichero no sabe nada de redes, de Samsung ni de HTTP: solo del negocio.
"""
from dataclasses import dataclass
from enum import Enum


class Estado(str, Enum):
    """Lo que sabemos de la pantalla. Solo tres respuestas honestas."""

    APAGADA = "apagada"        # certeza: no responde por red
    ENCENDIDA = "encendida"    # certeza: lleva respondiendo mas de lo que aguanta apagada
    DUDOSA = "dudosa"          # acaba de despertar: aun no se puede afirmar nada

    @property
    def es_certeza(self) -> bool:
        return self is not Estado.DUDOSA


class Tecla(str, Enum):
    """Teclas del mando que usamos por nombre propio.

    🚨 APAGAR es KEY_POWER, no KEY_POWEROFF: en este modelo KEY_POWEROFF no hace
    nada (probado el 2026-09-02; la tele se quedaba encendida y parecia un fallo
    de encendido posterior).
    """

    APAGAR = "KEY_POWER"
    ENCENDER = "KEY_POWERON"
    INICIO = "KEY_HOME"
    FUENTE = "KEY_SOURCE"
    VOLVER = "KEY_RETURN"
    ARRIBA = "KEY_UP"
    ABAJO = "KEY_DOWN"
    IZQUIERDA = "KEY_LEFT"
    DERECHA = "KEY_RIGHT"
    ACEPTAR = "KEY_ENTER"
    INFO = "KEY_INFO"
    CANAL_MAS = "KEY_CHUP"
    CANAL_MENOS = "KEY_CHDOWN"
    REPRODUCIR = "KEY_PLAY"
    PAUSA = "KEY_PAUSE"


@dataclass(frozen=True)
class Sonido:
    volumen: int
    silenciado: bool


@dataclass(frozen=True)
class Televisor:
    """La ficha de un televisor de la casa. Puede haber varios.

    Lo que lo identifica es la MAC, que no cambia nunca. La direccion (IP) no
    esta aqui a proposito: cambia cuando el router quiere (ver direccion.py).
    """

    id: str                    # para las direcciones web y las carpetas: "salon"
    nombre: str                # como lo llama la casa: "Salón"
    modelo: str                # lo que dice el propio aparato: "UE40NU7115"
    mac: str
    #: Los Samsung modernos dicen ellos mismos si la pantalla esta encendida.
    #: Los antiguos (el UE40NU7115) no, y hay que deducirlo (ver presencia.py).
    dice_su_estado: bool = False
    anadido: float = 0.0


@dataclass(frozen=True)
class Vistazo:
    """Lo que se saca de mirar al televisor una vez.

    `pantalla` es lo que dice el PROPIO aparato: True/False si lo publica, None
    si es de los que no lo dicen. Que conteste por red no significa que este
    encendido: en reposo muchos siguen contestando.
    """

    en_red: bool
    pantalla: bool | None = None

    @property
    def despierto(self) -> bool:
        """¿Puede recibir ordenes ahora? (teclas, sonido, aplicaciones)"""
        return self.en_red if self.pantalla is None else self.pantalla


@dataclass(frozen=True)
class Hallazgo:
    """Un televisor visto en la red de casa, este o no añadido al mando."""

    ip: str
    mac: str
    nombre: str
    modelo: str
    compatible: bool           # habla el protocolo que este mando sabe usar
    dice_su_estado: bool = False


class NoHayTalTelevisor(LookupError):
    def __init__(self, id: str | None = None) -> None:
        super().__init__(
            f"No hay ningún televisor «{id}» en este mando"
            if id
            else "Todavía no hay ningún televisor. Añade uno desde la web o con `anadir`."
        )


class NoEsUnTelevisor(ValueError):
    """En esa direccion no contesta un televisor que el mando sepa manejar."""


class YaEstaAnadido(ValueError):
    def __init__(self, televisor: "Televisor") -> None:
        super().__init__(f"Ese televisor ya está añadido: es «{televisor.nombre}»")
        self.televisor = televisor
