#!/usr/bin/env python3
"""Arranca el mando: la web y su API en el mismo sitio.

    python3 servir.py            # escucha en 0.0.0.0:8099
    MANDO_PUERTO=9000 python3 servir.py
"""
import os

import uvicorn

from mando_del_televisor.infraestructura.web.api_http import crear_aplicacion

if __name__ == "__main__":
    uvicorn.run(
        crear_aplicacion(),
        host=os.environ.get("MANDO_HOST", "0.0.0.0"),
        port=int(os.environ.get("MANDO_PUERTO", "8099")),
        log_level="warning",
    )
