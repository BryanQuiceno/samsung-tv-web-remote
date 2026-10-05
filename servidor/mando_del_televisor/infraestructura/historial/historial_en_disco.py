"""La memoria del vigia, en dos ficheros de texto plano y legibles a ojo.

  estado.json     -> la racha actual (una sola linea)
  historial.jsonl -> una muestra por linea, para poder dibujar las ultimas horas
                     y responder "¿desde cuando esta apagada?"

Se escribe con reemplazo atomico porque hay tres cosas anotando a la vez: el
vigia del cron cada minuto, la web y la linea de comandos.
"""
import json
import os
import time

from ...dominio.presencia import Muestra, Racha

HORAS_QUE_SE_GUARDAN = 24


class HistorialEnDisco:
    def __init__(self, carpeta: str) -> None:
        os.makedirs(carpeta, exist_ok=True)
        self._estado = os.path.join(carpeta, "estado.json")
        self._muestras = os.path.join(carpeta, "historial.jsonl")

    # ---------------------------------------------------------------- escribir
    def anotar(self, responde: bool) -> Racha:
        ahora = time.time()
        anterior = self.racha()

        if anterior is None or anterior.responde != responde:
            racha = Racha(responde=responde, desde=ahora, ultima_muestra=ahora)
        elif not anterior.esta_fresca(ahora):
            # el vigia estuvo parado: pudo pasar cualquier cosa en ese hueco,
            # asi que la racha vuelve a empezar en vez de mentir con su antiguedad
            racha = Racha(responde=responde, desde=ahora, ultima_muestra=ahora)
        else:
            racha = Racha(responde, anterior.desde, ahora, anterior.confirmada)

        self._guardar(racha)
        self._apuntar_muestra(ahora, responde)
        return racha

    def dar_por_confirmada(self) -> None:
        actual = self.racha()
        if actual and actual.responde:
            self._guardar(Racha(True, actual.desde, actual.ultima_muestra, confirmada=True))

    def romper(self) -> None:
        """Tras apagar: la racha y su confirmacion dejan de valer al instante."""
        ahora = time.time()
        self._guardar(Racha(responde=True, desde=ahora, ultima_muestra=ahora, confirmada=False))

    # ------------------------------------------------------------------- leer
    def racha(self) -> Racha | None:
        try:
            with open(self._estado) as fichero:
                d = json.load(fichero)
            return Racha(bool(d["responde"]), d["desde"], d["ultima_muestra"], bool(d.get("confirmada")))
        except Exception:
            return None

    def ultimas_muestras(self, minutos: int) -> list[Muestra]:
        desde = time.time() - minutos * 60
        muestras: list[Muestra] = []
        try:
            with open(self._muestras) as fichero:
                for linea in fichero:
                    try:
                        d = json.loads(linea)
                    except ValueError:
                        continue
                    if d["t"] >= desde:
                        muestras.append(Muestra(momento=d["t"], responde=bool(d["r"])))
        except OSError:
            pass
        return muestras

    # ---------------------------------------------------------------- privado
    def _guardar(self, racha: Racha) -> None:
        self._escribir_del_tiron(
            self._estado,
            json.dumps(
                {
                    "responde": racha.responde,
                    "desde": racha.desde,
                    "ultima_muestra": racha.ultima_muestra,
                    "confirmada": racha.confirmada,
                }
            ),
        )

    def _apuntar_muestra(self, momento: float, responde: bool) -> None:
        with open(self._muestras, "a") as fichero:
            fichero.write(json.dumps({"t": round(momento), "r": int(responde)}) + "\n")
        self._podar_si_toca()

    def _podar_si_toca(self) -> None:
        """El fichero crece una linea por minuto: se recorta de vez en cuando."""
        try:
            if os.path.getsize(self._muestras) < 300_000:
                return
            corte = time.time() - HORAS_QUE_SE_GUARDAN * 3600
            with open(self._muestras) as fichero:
                vivas = [l for l in fichero if _momento_de(l) >= corte]
            self._escribir_del_tiron(self._muestras, "".join(vivas))
        except OSError:
            pass

    @staticmethod
    def _escribir_del_tiron(destino: str, contenido: str) -> None:
        provisional = destino + ".tmp"
        with open(provisional, "w") as fichero:
            fichero.write(contenido)
        os.replace(provisional, destino)


def _momento_de(linea: str) -> float:
    try:
        return json.loads(linea)["t"]
    except Exception:
        return 0.0
