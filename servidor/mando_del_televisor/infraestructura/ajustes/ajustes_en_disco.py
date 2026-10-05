"""Los ajustes del mando, en un fichero de texto legible a ojo: datos/ajustes.json

Hay tres programas que lo leen (la web, el vigia del cron y la linea de
comandos) y cualquiera de ellos puede cambiarlo. Por eso cada lectura mira si el
fichero ha cambiado: la web, que lleva dias arrancada, se entera al momento de
que el vigia ha encontrado el televisor en otra direccion.
"""
import json
import os
import time

from ...dominio.direccion import SIN_DIRECCION, Direccion, Origen


class AjustesEnDisco:
    def __init__(self, carpeta: str, ip_de_fabrica: str) -> None:
        os.makedirs(carpeta, exist_ok=True)
        self._fichero = os.path.join(carpeta, "ajustes.json")
        self._de_fabrica = Direccion(ip=ip_de_fabrica)
        self._leido_cuando: float | None = None
        self._leido: Direccion = self._de_fabrica

    def direccion(self) -> Direccion:
        try:
            cuando = os.stat(self._fichero).st_mtime_ns
        except OSError:
            return self._de_fabrica          # nunca se ha cambiado nada
        if cuando != self._leido_cuando:
            self._leido = self._leer()
            self._leido_cuando = cuando
        return self._leido

    def cambiar_direccion(self, ip: str, origen: Origen) -> Direccion:
        anterior = self.direccion()
        nueva = Direccion(
            ip=ip,
            origen=origen,
            desde=time.time(),
            anterior=self._la_de_antes(anterior, ip),
        )
        provisional = self._fichero + ".tmp"
        with open(provisional, "w") as fichero:
            json.dump(
                {"ip": nueva.ip, "origen": nueva.origen.value, "desde": nueva.desde, "anterior": nueva.anterior},
                fichero,
            )
        os.replace(provisional, self._fichero)
        return nueva

    def _la_de_antes(self, anterior: Direccion, nueva: str) -> str | None:
        if anterior.ip == SIN_DIRECCION:
            return None                      # no habia ninguna: no hay "antes"
        return anterior.ip if anterior.ip != nueva else anterior.anterior

    def _leer(self) -> Direccion:
        try:
            with open(self._fichero) as fichero:
                d = json.load(fichero)
            return Direccion(d["ip"], Origen(d.get("origen", "a_mano")), d.get("desde"), d.get("anterior"))
        except Exception:
            return self._de_fabrica          # fichero roto: mejor lo de fabrica que nada
