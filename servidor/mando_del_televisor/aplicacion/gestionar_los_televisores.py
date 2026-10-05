"""Casos de uso: que televisores lleva este mando.

Añadir uno son dos pasos, y el segundo no se puede saltar ni hacer a distancia:
  1. encontrarlo en la red y apuntar quien es (su MAC, su modelo, donde esta);
  2. que ALGUIEN DELANTE acepte el aviso que sale en su pantalla. Sin eso el
     televisor no obedece a nadie: es su seguro contra mandos ajenos.
"""
import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Callable

from ..dominio.direccion import Origen, direccion_valida, misma_mac
from ..dominio.puertos import AjustesDelMando, CanalDeMando, CatalogoDeTelevisores, ExploradorDeTelevisores
from ..dominio.televisor import Hallazgo, NoEsUnTelevisor, Televisor, YaEstaAnadido


@dataclass(frozen=True)
class Visto:
    """Un televisor encontrado, y si ya lo lleva el mando."""

    hallazgo: Hallazgo
    ya_anadido: Televisor | None


class BuscarTelevisores:
    def __init__(self, explorador: ExploradorDeTelevisores, catalogo: CatalogoDeTelevisores) -> None:
        self._explorador = explorador
        self._catalogo = catalogo

    def __call__(self) -> list[Visto]:
        conocidos = self._catalogo.todos()
        return [Visto(h, _el_de_esa_mac(conocidos, h.mac)) for h in self._explorador.explorar()]


class AnadirUnTelevisor:
    def __init__(
        self,
        explorador: ExploradorDeTelevisores,
        catalogo: CatalogoDeTelevisores,
        ajustes_de: Callable[[str], AjustesDelMando],
    ) -> None:
        self._explorador = explorador
        self._catalogo = catalogo
        self._ajustes_de = ajustes_de

    def __call__(self, ip: str, nombre: str | None = None) -> Televisor:
        ip = direccion_valida(ip)
        hallazgo = self._explorador.mirar(ip)
        if hallazgo is None:
            raise NoEsUnTelevisor(
                f"En {ip} no contesta ningún televisor Samsung. Tiene que estar encendido para añadirlo."
            )
        if not hallazgo.compatible:
            raise NoEsUnTelevisor(
                f"El {hallazgo.modelo} de {ip} no acepta el mando por red: es un modelo anterior a los que se saben manejar."
            )

        conocidos = self._catalogo.todos()
        repetido = _el_de_esa_mac(conocidos, hallazgo.mac)
        if repetido:
            raise YaEstaAnadido(repetido)

        como_se_llama = (nombre or "").strip() or hallazgo.nombre
        televisor = Televisor(
            id=_identificador(como_se_llama, {t.id for t in conocidos}),
            nombre=como_se_llama,
            modelo=hallazgo.modelo,
            mac=hallazgo.mac,
            dice_su_estado=hallazgo.dice_su_estado,
            anadido=time.time(),
        )
        self._catalogo.anadir(televisor)
        self._ajustes_de(televisor.id).cambiar_direccion(ip, Origen.AL_ANADIRLO)
        return televisor


@dataclass(frozen=True)
class Emparejamiento:
    emparejado: bool
    mensaje: str


class EmparejarElTelevisor:
    """Pide permiso al televisor. Se queda esperando a que alguien lo acepte en la pantalla."""

    def __init__(self, canal: CanalDeMando) -> None:
        self._canal = canal

    def __call__(self) -> Emparejamiento:
        if self._canal.emparejar():
            return Emparejamiento(True, "Permiso concedido. Ya se puede manejar.")
        return Emparejamiento(
            False,
            "Nadie aceptó el aviso en la pantalla. Tiene que estar encendido y hay que "
            "elegir «Permitir» con su mando.",
        )


class QuitarUnTelevisor:
    def __init__(self, catalogo: CatalogoDeTelevisores) -> None:
        self._catalogo = catalogo

    def __call__(self, id: str) -> Televisor:
        televisor = self._catalogo.el(id)
        self._catalogo.quitar(id)
        return televisor


def _el_de_esa_mac(televisores: list[Televisor], mac: str) -> Televisor | None:
    return next((t for t in televisores if misma_mac(t.mac, mac)), None)


def _identificador(nombre: str, ocupados: set[str]) -> str:
    """«Salón de arriba» -> «salon-de-arriba». Si ya existe, «salon-de-arriba-2»."""
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "-", sin_tildes.lower()).strip("-") or "televisor"
    candidato, n = base, 1
    while candidato in ocupados:
        n += 1
        candidato = f"{base}-{n}"
    return candidato
