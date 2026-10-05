"""El reloj de verdad. Los casos de uso reciben esto en produccion y un doble en las pruebas."""
import time


class RelojDelSistema:
    def ahora(self) -> float:
        return time.time()

    def esperar(self, segundos: float) -> None:
        time.sleep(segundos)
