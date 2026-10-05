"""Composition root: el unico sitio donde se decide QUE adaptador usa cada puerto.

Todo lo de arriba (dominio y casos de uso) desconoce que hay Samsung, ficheros o
web. Cambiar aqui una linea basta para probar el sistema entero contra dobles.

Hay dos niveles:
  - `Casa`  : lo que es de todos (que televisores hay, buscar nuevos, añadir, quitar)
  - `Mando` : lo que es de UN televisor (encender, volumen, su vigia, su direccion)
"""
import json
import os
import threading
from dataclasses import dataclass
from typing import Callable

from .aplicacion.apagar_el_televisor import ApagarElTelevisor
from .aplicacion.confirmar_el_estado import ConfirmarElEstado
from .aplicacion.consultar_el_estado import ConsultarElEstado
from .aplicacion.controlar_el_sonido import AjustarElVolumen, SilenciarElTelevisor
from .aplicacion.encender_el_televisor import EncenderElTelevisor
from .aplicacion.gestionar_los_televisores import (
    AnadirUnTelevisor,
    BuscarTelevisores,
    EmparejarElTelevisor,
    QuitarUnTelevisor,
)
from .aplicacion.localizar_el_televisor import CambiarLaDireccion, LocalizarElTelevisor, SeguirAlTelevisor
from .aplicacion.poner_algo_en_netflix import PonerAlgoEnNetflix
from .aplicacion.pulsar_una_tecla import PulsarUnaTecla
from .dominio.direccion import SIN_DIRECCION
from .dominio.televisor import NoHayTalTelevisor, Televisor
from .infraestructura.ajustes.ajustes_en_disco import AjustesEnDisco
from .infraestructura.catalogo.catalogo_en_disco import CatalogoEnDisco
from .infraestructura.historial.historial_en_disco import HistorialEnDisco
from .infraestructura.red.buscador_por_vecinos import BuscadorPorVecinos
from .infraestructura.red.red_de_casa import RedDeCasa, red_de_casa
from .infraestructura.reloj_del_sistema import RelojDelSistema
from .infraestructura.samsung.altavoces_por_upnp import AltavocesPorUpnp
from .infraestructura.samsung.apps_por_dial import AppsPorDial
from .infraestructura.samsung.despertador_wake_on_lan import DespertadorWakeOnLan
from .infraestructura.samsung.explorador_samsung import ExploradorSamsung
from .infraestructura.samsung.mando_por_websocket import MandoPorWebSocket
from .infraestructura.samsung.sonda_rest import SondaRest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_DE_DATOS = os.environ.get("MANDO_DATOS", os.path.join(RAIZ, "datos"))



def titulos_de_netflix_de_la_casa() -> dict[str, str]:
    """Los titulos que esta casa pide por su nombre: `datos/netflix.json`.

        {"stranger things": "80057281"}

    El numero es el de la direccion del titulo en netflix.com. Si el fichero no
    existe no pasa nada: siempre se puede pasar el enlace entero.
    """
    try:
        with open(os.path.join(CARPETA_DE_DATOS, "netflix.json")) as fichero:
            return dict(json.load(fichero))
    except Exception:
        return {}


@dataclass
class Mando:
    """Todo lo que la web y la linea de comandos necesitan de UN televisor, ya montado."""

    televisor: Televisor
    consultar_el_estado: ConsultarElEstado
    confirmar_el_estado: ConfirmarElEstado
    encender: EncenderElTelevisor
    apagar: ApagarElTelevisor
    volumen: AjustarElVolumen
    silenciar: SilenciarElTelevisor
    pulsar: PulsarUnaTecla
    netflix: PonerAlgoEnNetflix
    emparejar: EmparejarElTelevisor
    historial: HistorialEnDisco
    sonda: SondaRest
    canal: MandoPorWebSocket
    altavoces: AltavocesPorUpnp
    ajustes: AjustesEnDisco
    localizar: LocalizarElTelevisor
    seguir_al_televisor: SeguirAlTelevisor
    cambiar_la_direccion: CambiarLaDireccion
    red: Callable[[], RedDeCasa]


def montar_el_mando(tele: Televisor, carpeta: str) -> Mando:
    """Monta el mando de un televisor cuyas cosas viven en `carpeta`."""
    # La direccion del televisor NO se fija al arrancar: se pregunta cada vez,
    # porque puede cambiar con el programa en marcha (ver dominio/direccion.py).
    ajustes = AjustesEnDisco(carpeta, ip_de_fabrica=SIN_DIRECCION)
    donde = lambda: ajustes.direccion().ip
    red = lambda: red_de_casa(hacia=donde())

    sonda = SondaRest(donde)
    despertador = DespertadorWakeOnLan(tele.mac, red)
    canal = MandoPorWebSocket(donde, os.path.join(carpeta, "token.txt"))
    altavoces = AltavocesPorUpnp(donde)
    apps = AppsPorDial(donde)
    historial = HistorialEnDisco(carpeta)
    reloj = RelojDelSistema()
    buscador = BuscadorPorVecinos(red)
    localizar = LocalizarElTelevisor(tele, ajustes, buscador, despertador, reloj)

    confirmar = ConfirmarElEstado(sonda, historial, reloj)

    return Mando(
        televisor=tele,
        consultar_el_estado=ConsultarElEstado(sonda, historial, altavoces, reloj),
        confirmar_el_estado=confirmar,
        encender=EncenderElTelevisor(despertador, sonda, canal, altavoces, historial, reloj, confirmar,
                                     reubicar=lambda: localizar(a_fondo=True)),
        apagar=ApagarElTelevisor(canal, sonda, historial),
        volumen=AjustarElVolumen(altavoces),
        silenciar=SilenciarElTelevisor(altavoces),
        pulsar=PulsarUnaTecla(canal, sonda),
        netflix=PonerAlgoEnNetflix(apps, sonda, titulos_de_netflix_de_la_casa),
        emparejar=EmparejarElTelevisor(canal),
        historial=historial,
        sonda=sonda,
        canal=canal,
        altavoces=altavoces,
        ajustes=ajustes,
        localizar=localizar,
        seguir_al_televisor=SeguirAlTelevisor(localizar, reloj),
        cambiar_la_direccion=CambiarLaDireccion(tele, ajustes, buscador, sonda),
        red=red,
    )


class Casa:
    """Los televisores de la casa y como se añaden y se quitan."""

    def __init__(self, carpeta_de_datos: str = CARPETA_DE_DATOS) -> None:
        self.catalogo = CatalogoEnDisco(carpeta_de_datos)
        self.red: Callable[[], RedDeCasa] = red_de_casa
        buscador = BuscadorPorVecinos(self.red)
        explorador = ExploradorSamsung(self.red, buscador)

        self.buscar_televisores = BuscarTelevisores(explorador, self.catalogo)
        self.anadir_un_televisor = AnadirUnTelevisor(
            explorador,
            self.catalogo,
            ajustes_de=lambda id: AjustesEnDisco(self.catalogo.carpeta_de(id), ip_de_fabrica=SIN_DIRECCION),
        )
        self._quitar = QuitarUnTelevisor(self.catalogo)
        self._mandos: dict[str, Mando] = {}
        self._cerrojo = threading.Lock()

    def televisores(self) -> list[Televisor]:
        return self.catalogo.todos()

    def mando(self, id: str | None = None) -> Mando:
        """El mando de un televisor. Sin decir cual, el primero que se añadio."""
        if id is None:
            todos = self.televisores()
            if not todos:
                raise NoHayTalTelevisor()
            id = todos[0].id
        tele = self.catalogo.el(id)          # falla aqui si lo han quitado
        with self._cerrojo:
            if id not in self._mandos:
                self._mandos[id] = montar_el_mando(tele, self.catalogo.carpeta_de(id))
            return self._mandos[id]

    def mandos(self) -> list[Mando]:
        return [self.mando(t.id) for t in self.televisores()]

    def quitar_un_televisor(self, id: str) -> Televisor:
        quitado = self._quitar(id)
        with self._cerrojo:
            self._mandos.pop(id, None)
        return quitado
