"""Encender tarda minutos. Esto lo saca del hilo del navegador y lo cuenta en vivo.

Hay UN televisor, asi que hay como mucho UNA operacion a la vez: no hace falta
una cola de trabajos, basta con recordar la que esta en marcha. Si llega una
segunda peticion mientras corre, se rechaza en vez de pisarla.
"""
import threading
import time
from dataclasses import asdict, dataclass, field


@dataclass
class Operacion:
    nombre: str
    mensaje: str = ""
    progreso: float = 0.0
    terminada: bool = False
    exito: bool | None = None
    empezada: float = field(default_factory=time.time)

    def como_json(self) -> dict:
        return asdict(self)


class OperacionEnCurso:
    def __init__(self) -> None:
        self._cerrojo = threading.Lock()
        self._actual: Operacion | None = None

    @property
    def actual(self) -> Operacion | None:
        return self._actual

    @property
    def hay_una_en_marcha(self) -> bool:
        op = self._actual
        return op is not None and not op.terminada

    def lanzar(self, nombre: str, tarea) -> Operacion:
        """`tarea(avisar)` corre en su propio hilo. Devuelve la operacion recien creada."""
        with self._cerrojo:
            if self.hay_una_en_marcha:
                raise YaHayUnaEnMarcha(self._actual.nombre)
            operacion = Operacion(nombre=nombre, mensaje="Empezando")
            self._actual = operacion

        def avisar(mensaje: str, progreso: float | None = None) -> None:
            operacion.mensaje = mensaje
            if progreso is not None:
                operacion.progreso = max(0.0, min(1.0, progreso))

        def envolver() -> None:
            try:
                resultado = tarea(avisar)
                operacion.exito = getattr(resultado, "encendida", True)
                operacion.mensaje = getattr(resultado, "mensaje", operacion.mensaje)
            except Exception as error:
                operacion.exito = False
                operacion.mensaje = f"No salio bien: {error}"
            finally:
                operacion.progreso = 1.0
                operacion.terminada = True

        threading.Thread(target=envolver, daemon=True, name=f"mando-{nombre}").start()
        return operacion


class YaHayUnaEnMarcha(Exception):
    def __init__(self, nombre: str) -> None:
        super().__init__(f"Espera: ya se esta {nombre}")
