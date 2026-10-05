"""Los puertos: lo que el dominio necesita del mundo, dicho en sus palabras.

Cada uno tiene su adaptador en `infraestructura/`. El dominio y los casos de uso
solo conocen estas interfaces, asi que se pueden probar con dobles y se puede
cambiar la forma de hablar con el televisor sin tocar las reglas.
"""
from typing import Protocol

from .direccion import Direccion, Origen
from .presencia import Muestra, Racha
from .televisor import Hallazgo, Sonido, Tecla, Televisor, Vistazo


class SondaDeRed(Protocol):
    """Mirar al televisor sin tocarlo: ¿contesta? ¿y dice si esta encendido?"""

    def mirar(self) -> Vistazo: ...
    def responde(self) -> bool: ...        # atajo: ¿contesta por red?


class DespertadorDeRed(Protocol):
    """Despierta la tarjeta de red del televisor (Wake-on-LAN)."""

    def despertar(self) -> None: ...


class CanalDeMando(Protocol):
    """El canal por el que se pulsan teclas, como el mando de infrarrojos."""

    def pulsar(self, tecla: Tecla) -> None: ...
    def emparejar(self) -> bool: ...
    def esta_emparejado(self) -> bool: ...


class Altavoces(Protocol):
    """Volumen y silencio. Solo responden con el televisor despierto."""

    def leer(self) -> Sonido: ...
    def poner_volumen(self, volumen: int) -> None: ...
    def silenciar(self, silenciado: bool) -> None: ...
    def estan_disponibles(self) -> bool: ...


class LanzadorDeApps(Protocol):
    """Abre una aplicacion del televisor y, si se puede, en un contenido concreto."""

    def lanzar(self, app: str, contenido: str | None = None) -> None: ...
    def esta_abierta(self, app: str) -> bool: ...


class HistorialDePresencia(Protocol):
    """La memoria de quien vigila: quien sabe cuanto lleva el televisor asi."""

    def anotar(self, responde: bool) -> Racha: ...
    def racha(self) -> Racha | None: ...
    def dar_por_confirmada(self) -> None: ...
    def romper(self) -> None: ...
    def ultimas_muestras(self, minutos: int) -> list[Muestra]: ...


class Reloj(Protocol):
    """El tiempo, inyectado: asi los casos de uso se prueban sin esperar de verdad."""

    def ahora(self) -> float: ...
    def esperar(self, segundos: float) -> None: ...


class AjustesDelMando(Protocol):
    """Lo que el mando recuerda entre un arranque y otro: donde esta el televisor."""

    def direccion(self) -> Direccion: ...
    def cambiar_direccion(self, ip: str, origen: Origen) -> Direccion: ...


class BuscadorEnLaRed(Protocol):
    """Encuentra un aparato por su MAC, que es lo unico suyo que no cambia."""

    def donde_esta(self, mac: str, a_fondo: bool = False) -> str | None: ...
    def quien_contesta_en(self, ip: str) -> str | None: ...


class CatalogoDeTelevisores(Protocol):
    """Los televisores que este mando conoce."""

    def todos(self) -> list[Televisor]: ...
    def el(self, id: str) -> Televisor: ...
    def anadir(self, televisor: Televisor) -> None: ...
    def quitar(self, id: str) -> None: ...


class ExploradorDeTelevisores(Protocol):
    """Encuentra televisores en la red de casa preguntandoles a ellos mismos."""

    def explorar(self) -> list[Hallazgo]: ...
    def mirar(self, ip: str) -> Hallazgo | None: ...
