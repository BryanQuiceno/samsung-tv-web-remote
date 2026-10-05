#!/usr/bin/env python3
"""El vigia: anota cada minuto si cada televisor responde. Lo llama el cron.

Sin el, el sistema no puede distinguir "encendida" de "apagada echando el ultimo
coletazo de red", porque esa distincion solo existe en el tiempo.

Tambien es quien evita quedarse sin mando: si un televisor no contesta, antes de
apuntar "sin respuesta" mira si es que ha cambiado de direccion, y lo sigue.
"""
from mando_del_televisor.composicion import Casa

if __name__ == "__main__":
    for mando in Casa().mandos():
        try:
            vistazo = mando.sonda.mirar()
            if not vistazo.en_red and mando.seguir_al_televisor().cambiada:
                vistazo = mando.sonda.mirar()
            racha = mando.historial.anotar(vistazo.despierto)
            print(mando.televisor.nombre + ":", "responde" if racha.responde else "sin respuesta",
                  f"desde hace {int(racha.ultima_muestra - racha.desde)} s")
        except Exception as error:            # un televisor roto no deja sin vigia a los demas
            print(mando.televisor.nombre + ":", "error", error)
