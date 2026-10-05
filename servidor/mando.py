#!/usr/bin/env python3
"""Mando del televisor por linea de comandos.

Es la MISMA maquinaria que usa la web: solo cambia por donde entran las ordenes
y como se cuentan. Si la web y esto discreparan alguna vez, seria un fallo.

    mando estado | info | on | off | vol [N|+N|-N] | mute [on|off] | tecla NOMBRE | teclas
    mando netflix <enlace de Netflix> | netflix "nombre guardado" | netflix
    mando buscar | ip [DIRECCION]
    mando televisores | descubrir | anadir DIRECCION [NOMBRE] | emparejar | quitar

Con varios televisores, se dice cual delante de la orden:  mando --tv salon on
Sin decirlo, se entiende el primero que se añadio.
"""
import json
import sys

from mando_del_televisor.aplicacion.controlar_el_sonido import TelevisorDormido
from mando_del_televisor.composicion import Casa
from mando_del_televisor.dominio.direccion import DireccionNoValida, EsOtroAparato
from mando_del_televisor.dominio.televisor import NoEsUnTelevisor, NoHayTalTelevisor, YaEstaAnadido
from mando_del_televisor.dominio.televisor import Estado, Tecla

USO = "\n".join(l.strip() for l in __doc__.strip().splitlines()[5:9])


def _contar(mensaje: str, progreso: float | None = None) -> None:
    print(mensaje, flush=True)


def principal(argumentos: list[str]) -> int:
    if not argumentos:
        print(USO)
        return 1

    casa = Casa()
    cual = None
    if argumentos[0] == "--tv":
        if len(argumentos) < 3:
            print(USO)
            return 1
        cual, argumentos = argumentos[1], argumentos[2:]
    orden, resto = argumentos[0], argumentos[1:]

    # ---- lo que es de la casa entera, no de un televisor
    if orden == "televisores":
        for m in casa.mandos():
            t = m.televisor
            print(f"{t.id}\t{t.nombre}\t{t.modelo}\t{m.ajustes.direccion().ip}")
        return 0

    if orden == "descubrir":
        vistos = casa.buscar_televisores()
        for v in vistos:
            h = v.hallazgo
            nota = f"ya añadido como «{v.ya_anadido.nombre}»" if v.ya_anadido else ("se puede añadir" if h.compatible else "no compatible")
            print(f"{h.ip}\t{h.nombre}\t{h.modelo}\t{nota}")
        if not vistos:
            print("No veo ningún televisor Samsung encendido en la red de casa.")
        return 0

    if orden == "anadir":
        if not resto:
            print(USO)
            return 1
        try:
            tele = casa.anadir_un_televisor(resto[0], " ".join(resto[1:]) or None)
        except (DireccionNoValida, NoEsUnTelevisor, YaEstaAnadido) as error:
            print(error, file=sys.stderr)
            return 1
        print(f"Añadido «{tele.nombre}» ({tele.modelo}) como {tele.id}.")
        print("Ahora mira su pantalla y elige «Permitir» con su mando...", flush=True)
        resultado = casa.mando(tele.id).emparejar()
        print(resultado.mensaje)
        return 0 if resultado.emparejado else 1

    try:
        mando = casa.mando(cual)
    except NoHayTalTelevisor as error:
        print(error, file=sys.stderr)
        return 1

    if orden == "quitar":
        print(f"Quitado «{casa.quitar_un_televisor(mando.televisor.id).nombre}». Sus datos quedan en datos/quitados.")
        return 0

    if orden == "emparejar":
        print("Mira su pantalla y elige «Permitir» con su mando...", flush=True)
        resultado = mando.emparejar()
        print(resultado.mensaje)
        return 0 if resultado.emparejado else 1
    # nombres antiguos de la skill, para no romper lo que ya se usa
    orden = {"status": "estado", "key": "tecla", "keys": "teclas", "mute": "mute"}.get(orden, orden)

    if orden == "estado":
        situacion = mando.consultar_el_estado()
        if situacion.estado is Estado.DUDOSA:
            print("La red acaba de despertar; lo compruebo (~2 min)...", flush=True)
            print(mando.confirmar_el_estado(_contar).value)
        else:
            print(situacion.estado.value)

    elif orden == "on":
        resultado = mando.encender(_contar)
        print(resultado.mensaje)
        return 0 if resultado.encendida else 1

    elif orden == "off":
        print(mando.apagar().mensaje)

    elif orden == "vol":
        try:
            if not resto:
                situacion = mando.consultar_el_estado()
                print(situacion.sonido.volumen if situacion.sonido else "el televisor esta apagado")
            elif resto[0][0] in "+-":
                print(mando.volumen.subir(int(resto[0])).volumen)
            else:
                print(mando.volumen.a(int(resto[0])).volumen)
        except TelevisorDormido as error:
            print(error, file=sys.stderr)
            return 1

    elif orden == "mute":
        try:
            deseado = None if not resto else resto[0] == "on"
            print("on" if mando.silenciar(deseado).silenciado else "off")
        except TelevisorDormido as error:
            print(error, file=sys.stderr)
            return 1

    elif orden == "tecla":
        if not resto:
            print(USO)
            return 1
        mando.pulsar(Tecla[resto[0].upper()])
        print("pulsada")

    elif orden == "info":
        situacion = mando.consultar_el_estado()
        print(json.dumps({
            "estado": situacion.estado.value,
            "segundosEnEsteEstado": round(situacion.segundos_en_este_estado),
            "volumen": situacion.sonido.volumen if situacion.sonido else None,
            "silenciado": situacion.sonido.silenciado if situacion.sonido else None,
            "id": mando.televisor.id,
            "nombre": mando.televisor.nombre,
            "televisor": mando.televisor.modelo,
            "ip": mando.ajustes.direccion().ip,
            "mac": mando.televisor.mac,
        }, ensure_ascii=False, indent=2))

    elif orden == "netflix":
        from mando_del_televisor.aplicacion.poner_algo_en_netflix import (
            TelevisorDormido as NetflixConTelevisorDormido,
        )
        try:
            print(mando.netflix(" ".join(resto) if resto else None))
        except (NetflixConTelevisorDormido, ValueError) as error:
            print(error, file=sys.stderr)
            return 1

    elif orden == "buscar":
        # busca el televisor por su MAC en toda la red de casa y apunta donde esta
        hallazgo = mando.localizar(a_fondo=True, despertando=True)
        print(hallazgo.mensaje)
        return 0 if hallazgo.encontrada else 1

    elif orden == "ip":
        if not resto:
            print(mando.ajustes.direccion().ip)
        else:
            try:
                print(mando.cambiar_la_direccion(resto[0]).mensaje)
            except (DireccionNoValida, EsOtroAparato) as error:
                print(error, file=sys.stderr)
                return 1

    elif orden == "teclas":
        print(json.dumps([t.name for t in Tecla], ensure_ascii=False))

    else:
        print(USO)
        return 1

    return 0


if __name__ == "__main__":
    try:
        sys.exit(principal(sys.argv[1:]))
    except KeyError as error:
        print(f"No conozco esa tecla: {error}", file=sys.stderr)
        sys.exit(2)
    except Exception as error:
        print(f"error: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(2)
