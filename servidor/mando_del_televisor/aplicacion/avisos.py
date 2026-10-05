"""Como un caso de uso largo cuenta por donde va.

Encender tarda minutos porque hay que CONFIRMAR que la pantalla se quedo
encendida. Sin esto, la web solo podria mostrar una ruleta sin informacion.
"""
from typing import Callable, Protocol


class Aviso(Protocol):
    def __call__(self, mensaje: str, progreso: float | None = None) -> None: ...


def en_silencio(mensaje: str, progreso: float | None = None) -> None:
    """Aviso por defecto: no cuenta nada. Lo usa la linea de comandos."""
