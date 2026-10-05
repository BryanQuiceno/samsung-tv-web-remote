"""La puerta HTTP: traduce peticiones del navegador a casos de uso y al reves.

Esta capa no decide nada del negocio. Si aqui aparece una regla ("si lleva mas
de X segundos..."), esta en el sitio equivocado: va en `dominio` o `aplicacion`.

Las direcciones dicen de que va cada cosa:
    /api/televisores                 los que hay, buscar nuevos, añadir
    /api/televisores/{id}/...        todo lo que se le hace a UNO
"""
import os
import time

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ...aplicacion.consultar_el_estado import Situacion
from ...aplicacion.controlar_el_sonido import TelevisorDormido
from ...aplicacion.localizar_el_televisor import Localizacion
from ...aplicacion.poner_algo_en_netflix import TelevisorDormido as NetflixConTelevisorDormido
from ...aplicacion.pulsar_una_tecla import TelevisorDormido as TeclaConTelevisorDormido
from ...composicion import Casa, Mando
from ...dominio.direccion import DireccionNoValida, EsOtroAparato
from ...dominio.presencia import RACHA_PARA_FIARSE
from ...dominio.televisor import NoEsUnTelevisor, NoHayTalTelevisor, Tecla, Televisor, YaEstaAnadido
from .operacion_en_curso import OperacionEnCurso, YaHayUnaEnMarcha

MINUTOS_DE_HISTORIAL = 90

casa = Casa()
#: Cada televisor tiene su propia operacion larga: encender el del salon no
#: impide apagar el del dormitorio.
operaciones: dict[str, OperacionEnCurso] = {}

api = APIRouter(prefix="/api")


class UnTelevisor:
    """Lo que necesita cualquier peticion sobre un televisor concreto."""

    def __init__(self, id: str) -> None:
        try:
            self.mando: Mando = casa.mando(id)
        except NoHayTalTelevisor as error:
            raise HTTPException(status_code=404, detail=str(error))
        self.operacion = operaciones.setdefault(id, OperacionEnCurso())


uno = APIRouter(prefix="/televisores/{id}")


# --------------------------------------------------------------- lo que sale
def _televisor_como_json(mando: Mando) -> dict:
    tele: Televisor = mando.televisor
    return {
        "id": tele.id,
        "nombre": tele.nombre,
        "modelo": tele.modelo,
        "ip": mando.ajustes.direccion().ip,
        "emparejado": mando.canal.esta_emparejado(),
    }


def _situacion_como_json(situacion: Situacion) -> dict:
    racha = situacion.racha
    return {
        "estado": situacion.estado.value,
        "esCerteza": situacion.estado.es_certeza,
        "segundosEnEsteEstado": round(situacion.segundos_en_este_estado),
        "segundosParaFiarse": round(RACHA_PARA_FIARSE),
        "sonido": (
            {"volumen": situacion.sonido.volumen, "silenciado": situacion.sonido.silenciado}
            if situacion.sonido
            else None
        ),
        "confirmada": bool(racha and racha.confirmada),
    }


class PeticionDeVolumen(BaseModel):
    volumen: int | None = Field(default=None, ge=0, le=100)
    paso: int | None = None


class PeticionDeSilencio(BaseModel):
    silenciado: bool | None = None


class PeticionDeTecla(BaseModel):
    tecla: str


class PeticionDeNetflix(BaseModel):
    titulo: str | None = None


class PeticionDeDireccion(BaseModel):
    ip: str


class PeticionDeAlta(BaseModel):
    ip: str
    nombre: str | None = Field(default=None, max_length=40)


# ------------------------------------------------------------ los televisores
@api.get("/televisores")
def televisores() -> dict:
    return {"televisores": [_televisor_como_json(m) for m in casa.mandos()]}


@api.post("/televisores/buscar")
def buscar_televisores() -> dict:
    """Los Samsung que hay ahora mismo en la red de casa. Tarda unos segundos."""
    return {
        "hallados": [
            {
                "ip": v.hallazgo.ip,
                "nombre": v.hallazgo.nombre,
                "modelo": v.hallazgo.modelo,
                "compatible": v.hallazgo.compatible,
                "yaAnadido": v.ya_anadido.nombre if v.ya_anadido else None,
            }
            for v in casa.buscar_televisores()
        ]
    }


@api.post("/televisores", status_code=201)
def anadir_un_televisor(peticion: PeticionDeAlta) -> dict:
    """Lo apunta. Aun falta que alguien acepte el aviso en su pantalla (`/emparejar`)."""
    try:
        tele = casa.anadir_un_televisor(peticion.ip, peticion.nombre)
    except (DireccionNoValida, NoEsUnTelevisor) as error:
        raise HTTPException(status_code=400, detail=str(error))
    except YaEstaAnadido as error:
        raise HTTPException(status_code=409, detail=str(error))
    return _televisor_como_json(casa.mando(tele.id))


@uno.post("/emparejar")
def emparejar(tv: UnTelevisor = Depends()) -> dict:
    """Se queda esperando (hasta 45 s) a que alguien acepte el aviso en la pantalla."""
    resultado = tv.mando.emparejar()
    return {"emparejado": resultado.emparejado, "mensaje": resultado.mensaje}


@uno.delete("")
def quitar(tv: UnTelevisor = Depends()) -> dict:
    if tv.operacion.hay_una_en_marcha:
        raise HTTPException(status_code=409, detail="Espera: hay una orden en marcha")
    quitado = casa.quitar_un_televisor(tv.mando.televisor.id)
    operaciones.pop(quitado.id, None)
    return {"quitado": quitado.nombre}


# ------------------------------------------------------------------- estado
@uno.get("/estado")
def estado(tv: UnTelevisor = Depends()) -> dict:
    situacion = tv.mando.consultar_el_estado()
    respuesta = _situacion_como_json(situacion)
    op = tv.operacion.actual
    respuesta["operacion"] = op.como_json() if op else None
    respuesta["televisor"] = _televisor_como_json(tv.mando)
    return respuesta


@uno.get("/presencia")
def presencia(tv: UnTelevisor = Depends()) -> dict:
    """Las ultimas horas de vigilancia, para dibujar la tira del vigia."""
    muestras = tv.mando.historial.ultimas_muestras(MINUTOS_DE_HISTORIAL)
    return {
        "desde": muestras[0].momento if muestras else time.time(),
        "minutos": MINUTOS_DE_HISTORIAL,
        "muestras": [{"t": round(m.momento), "responde": m.responde} for m in muestras],
    }


# ------------------------------------------------------------------ encender
@uno.post("/encender")
def encender(tv: UnTelevisor = Depends()) -> dict:
    try:
        op = tv.operacion.lanzar("encendiendo", tv.mando.encender)
    except YaHayUnaEnMarcha as error:
        raise HTTPException(status_code=409, detail=str(error))
    return op.como_json()


@uno.post("/apagar")
def apagar(tv: UnTelevisor = Depends()) -> dict:
    if tv.operacion.hay_una_en_marcha:
        raise HTTPException(status_code=409, detail="Espera: hay una orden en marcha")
    resultado = tv.mando.apagar()
    return {"mensaje": resultado.mensaje, "yaEstabaApagada": resultado.ya_estaba_apagada}


@uno.post("/confirmar")
def confirmar(tv: UnTelevisor = Depends()) -> dict:
    """Resuelve un estado dudoso mirando un par de minutos."""
    try:
        op = tv.operacion.lanzar("confirmando", lambda avisar: tv.mando.confirmar_el_estado(avisar))
    except YaHayUnaEnMarcha as error:
        raise HTTPException(status_code=409, detail=str(error))
    return op.como_json()


# -------------------------------------------------------------------- sonido
@uno.post("/volumen")
def volumen(peticion: PeticionDeVolumen, tv: UnTelevisor = Depends()) -> dict:
    try:
        if peticion.volumen is not None:
            sonido = tv.mando.volumen.a(peticion.volumen)
        elif peticion.paso:
            ajustar = tv.mando.volumen
            sonido = ajustar.subir(peticion.paso) if peticion.paso > 0 else ajustar.bajar(-peticion.paso)
        else:
            raise HTTPException(status_code=400, detail="Falta el volumen o el paso")
        return {"volumen": sonido.volumen, "silenciado": sonido.silenciado}
    except TelevisorDormido as error:
        raise HTTPException(status_code=409, detail=str(error))


@uno.post("/silencio")
def silencio(peticion: PeticionDeSilencio, tv: UnTelevisor = Depends()) -> dict:
    try:
        sonido = tv.mando.silenciar(peticion.silenciado)
        return {"volumen": sonido.volumen, "silenciado": sonido.silenciado}
    except TelevisorDormido as error:
        raise HTTPException(status_code=409, detail=str(error))


# -------------------------------------------------------------------- teclas
@uno.post("/tecla")
def tecla(peticion: PeticionDeTecla, tv: UnTelevisor = Depends()) -> dict:
    try:
        pulsada = Tecla[peticion.tecla]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"No conozco la tecla «{peticion.tecla}»")
    try:
        tv.mando.pulsar(pulsada)
    except TeclaConTelevisorDormido as error:
        raise HTTPException(status_code=409, detail=str(error))
    except Exception:
        raise HTTPException(status_code=502, detail=_no_obedece(tv.mando))
    return {"pulsada": pulsada.name}


@uno.post("/netflix")
def netflix(peticion: PeticionDeNetflix, tv: UnTelevisor = Depends()) -> dict:
    """Abre Netflix, y si se dice en que titulo, directamente ahi."""
    try:
        return {"mensaje": tv.mando.netflix(peticion.titulo)}
    except NetflixConTelevisorDormido as error:
        raise HTTPException(status_code=409, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@api.get("/teclas")
def teclas() -> dict:
    return {"teclas": [t.name for t in Tecla]}


def _no_obedece(mando: Mando) -> str:
    if not mando.canal.esta_emparejado():
        return "Este televisor aún no ha dado permiso. Dáselo desde Ajustes."
    return "El televisor no ha aceptado la orden"


# ------------------------------------------------------------------- ajustes
def _ajustes_como_json(mando: Mando, hallazgo: Localizacion | None = None) -> dict:
    direccion = mando.ajustes.direccion()
    red = mando.red()
    respuesta = {
        "televisor": {
            "ip": direccion.ip,
            "mac": mando.televisor.mac,
            "origen": direccion.origen.value,
            "desde": direccion.desde,
            "anterior": direccion.anterior,
            "emparejado": mando.canal.esta_emparejado(),
        },
        "servidor": {"ip": red.ip, "interfaz": red.interfaz},
    }
    if hallazgo:
        respuesta["resultado"] = {
            "encontrada": hallazgo.encontrada,
            "cambiada": hallazgo.cambiada,
            "mensaje": hallazgo.mensaje,
        }
    return respuesta


@uno.get("/ajustes")
def ajustes(tv: UnTelevisor = Depends()) -> dict:
    """Donde cree el mando que esta el televisor, y como lo supo."""
    return _ajustes_como_json(tv.mando)


@uno.post("/ajustes/buscar")
def buscar_el_televisor(tv: UnTelevisor = Depends()) -> dict:
    """Lo busca por su MAC en toda la red de casa. Tarda unos segundos."""
    if tv.operacion.hay_una_en_marcha:
        raise HTTPException(status_code=409, detail="Espera: hay una orden en marcha")
    return _ajustes_como_json(tv.mando, tv.mando.localizar(a_fondo=True, despertando=True))


@uno.post("/ajustes/direccion")
def cambiar_la_direccion(peticion: PeticionDeDireccion, tv: UnTelevisor = Depends()) -> dict:
    try:
        return _ajustes_como_json(tv.mando, tv.mando.cambiar_la_direccion(peticion.ip))
    except DireccionNoValida as error:
        raise HTTPException(status_code=400, detail=str(error))
    except EsOtroAparato as error:
        raise HTTPException(status_code=409, detail=str(error))


api.include_router(uno)


# ---------------------------------------------------------------- la web
def _donde_esta_la_web() -> str:
    """La web compilada vive en `web/dist`, al lado de `servidor/`."""
    aqui = os.path.abspath(__file__)
    raiz_del_proyecto = os.path.abspath(os.path.join(aqui, *[os.pardir] * 5))
    return os.path.join(raiz_del_proyecto, "web", "dist")


def crear_aplicacion() -> FastAPI:
    aplicacion = FastAPI(title="Mando del televisor", docs_url="/api/docs")
    aplicacion.include_router(api)

    portada = _donde_esta_la_web()
    if os.path.isdir(portada):
        # Cualquier direccion que no sea de la API devuelve la pagina: asi el
        # movil puede guardar el acceso directo en cualquier ruta y sigue yendo.
        @aplicacion.get("/{camino:path}")
        def pagina(camino: str):
            fichero = os.path.normpath(os.path.join(portada, camino))
            if camino and fichero.startswith(portada) and os.path.isfile(fichero):
                return FileResponse(fichero)
            return FileResponse(os.path.join(portada, "index.html"))

    return aplicacion
