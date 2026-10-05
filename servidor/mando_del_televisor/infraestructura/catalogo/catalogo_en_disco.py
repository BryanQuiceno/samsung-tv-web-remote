"""Los televisores de la casa, cada uno en su carpeta de `datos/televisores/`.

    datos/televisores/salon/
        televisor.json    quien es: nombre, modelo y MAC
        ajustes.json      donde esta hoy (la direccion cambia; ver dominio/direccion.py)
        token.txt         el permiso que dio alguien aceptando el aviso en la pantalla
        estado.json       \\  la memoria del vigia
        historial.jsonl   /

Todo lo de un televisor vive junto: añadir uno es crear una carpeta y quitarlo
es apartarla. No se borra nada: lo quitado va a `datos/quitados/`, con su
permiso incluido, por si fue sin querer.
"""
import json
import os
import time

from ...dominio.televisor import NoHayTalTelevisor, Televisor


class CatalogoEnDisco:
    def __init__(self, carpeta_de_datos: str) -> None:
        self._raiz = os.path.join(carpeta_de_datos, "televisores")
        self._quitados = os.path.join(carpeta_de_datos, "quitados")
        os.makedirs(self._raiz, exist_ok=True)

    def carpeta_de(self, id: str) -> str:
        return os.path.join(self._raiz, id)

    def todos(self) -> list[Televisor]:
        teles = []
        for id in os.listdir(self._raiz):
            try:
                teles.append(self._leer(id))
            except Exception:
                continue          # una carpeta a medias no tumba a los demas
        return sorted(teles, key=lambda t: (t.anadido, t.id))

    def el(self, id: str) -> Televisor:
        try:
            return self._leer(id)
        except Exception:
            raise NoHayTalTelevisor(id)

    def anadir(self, televisor: Televisor) -> None:
        carpeta = self.carpeta_de(televisor.id)
        os.makedirs(carpeta, exist_ok=True)
        provisional = os.path.join(carpeta, "televisor.json.tmp")
        with open(provisional, "w") as fichero:
            json.dump(
                {
                    "nombre": televisor.nombre,
                    "modelo": televisor.modelo,
                    "mac": televisor.mac,
                    "dice_su_estado": televisor.dice_su_estado,
                    "anadido": televisor.anadido or time.time(),
                },
                fichero,
                ensure_ascii=False,
                indent=2,
            )
        os.replace(provisional, os.path.join(carpeta, "televisor.json"))

    def quitar(self, id: str) -> None:
        self.el(id)
        os.makedirs(self._quitados, exist_ok=True)
        os.replace(self.carpeta_de(id), os.path.join(self._quitados, f"{id}-{int(time.time())}"))

    def _leer(self, id: str) -> Televisor:
        if os.sep in id or id.startswith("."):
            raise NoHayTalTelevisor(id)
        with open(os.path.join(self._raiz, id, "televisor.json")) as fichero:
            d = json.load(fichero)
        return Televisor(
            id=id,
            nombre=d["nombre"],
            modelo=d.get("modelo", ""),
            mac=d["mac"],
            dice_su_estado=bool(d.get("dice_su_estado")),
            anadido=d.get("anadido", 0.0),
        )
