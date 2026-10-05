# Architecture

The code is written in **Spanish**: folders, classes, functions and comments. That is deliberate — the folders are meant to *say what the thing is about* ("screaming architecture") in the language of the people who use it. This page is the map for everyone else.

The layering is: **vertical slice → hexagonal (ports and adapters) → screaming architecture**. There is one slice, `mando_del_televisor` ("the TV's remote"), split in three layers that only depend inwards.

```
servidor/                                  the server ("servidor")
  servir.py                                starts the web UI + API (uvicorn)
  mando.py                                 the command line
  vigia.py                                 the watcher, run by cron every minute
  pruebas/                                 unit tests, against doubles
  mando_del_televisor/
    dominio/                               DOMAIN: business rules, knows nothing of networks or Samsung
      televisor.py                           the TV, its states and keys
      presencia.py                           the streak over time and the measurements behind it
      direccion.py                           where the TV is today (IP) and who said so
      puertos.py                             PORTS: the interfaces the domain needs from the world
    aplicacion/                            APPLICATION: one file per use case
      encender_el_televisor.py               power on: wake + key + VERIFY + retry
      apagar_el_televisor.py                 power off
      consultar_el_estado.py                 what state is it in?
      confirmar_el_estado.py                 resolve an "unsure" state by watching
      controlar_el_sonido.py                 volume and mute
      pulsar_una_tecla.py                    press a key
      poner_algo_en_netflix.py               open Netflix on a title
      localizar_el_televisor.py              find it by MAC and follow it when its IP changes
      gestionar_los_televisores.py           discover, add, pair and remove TVs
    infraestructura/                       ADAPTERS: the only part that knows about Samsung, files or HTTP
      samsung/                               REST probe, WebSocket keys, Wake-on-LAN, UPnP audio, DIAL, scanner
      red/                                   the OS neighbour table and the LAN interface
      catalogo/                              the TVs of the house, one folder each
      ajustes/                               each TV's address, in its ajustes.json
      historial/                             the watcher's memory, in text files
      web/                                   FastAPI routes and background operations
    composicion.py                         COMPOSITION ROOT: the only place that picks an adapter for each port

web/                                       React + Vite + TypeScript, same split
  src/dominio/                               the vocabulary shared with the server
  src/aplicacion/                            hooks: the "when" of the screen
  src/infraestructura/                       the HTTP client — the only file that knows HTTP exists
  src/ui/                                    components, each with its CSS next to it
```

**The rule:** if a business decision ("if it has been answering for more than X seconds…") shows up outside `dominio/` or `aplicacion/`, it is in the wrong place.

## The two objects that matter

`composicion.py` builds two things:

- **`Casa`** ("house"): what belongs to everyone — the list of TVs, discovering, adding, removing.
- **`Mando`** ("remote"): everything for **one** TV, already wired — its use cases, its probe, its address, its watcher history.

The web API, the CLI and the watcher are three thin entry points over the same `Casa`. If the web UI and the CLI ever disagree, that is a bug.

## Identity versus address

A TV **is** its MAC address; its IP is only "where it is today". Nothing holds an IP at start-up: every adapter receives a function and asks for the current address on each call. So when the watcher (a separate cron process) discovers the TV at a new IP and writes `ajustes.json`, the long-running web server picks it up on its next request, with no restart.

## Glossary (Spanish → English)

| Spanish | English | Where |
|---|---|---|
| mando | remote control | everywhere |
| televisor, tele | TV | |
| casa | house / home | `Casa` in `composicion.py` |
| encender / apagar | power on / power off | use cases |
| encendida / apagada / dudosa | on / off / unsure | `Estado` |
| tecla / pulsar | key / to press | `Tecla`, `PulsarUnaTecla` |
| sonido / volumen / silenciar | sound / volume / mute | |
| vigía | watcher (the cron job) | `vigia.py` |
| presencia / racha / muestra | presence / streak / sample | `presencia.py` |
| sonda / vistazo | probe / a single look | `SondaDeRed`, `Vistazo` |
| despertador | waker (Wake-on-LAN) | `DespertadorDeRed` |
| canal | channel (the key WebSocket) | `CanalDeMando` |
| altavoces | speakers (UPnP audio) | `Altavoces` |
| emparejar / permiso | to pair / permission | pairing token |
| dirección | address (IP) | `direccion.py` |
| buscador / vecinos | finder / neighbours (ARP table) | `BuscadorPorVecinos` |
| explorador / hallazgo | scanner / a find | `ExploradorSamsung`, `Hallazgo` |
| catálogo | catalogue (configured TVs) | `CatalogoEnDisco` |
| ajustes | settings | |
| añadir / quitar | add / remove | |
| puerto (dominio) | port (hexagonal sense) | `puertos.py` |
| pruebas / dobles | tests / test doubles | `servidor/pruebas/` |
| despliegue | deployment | `despliegue/` |
| datos | data | `servidor/datos/` |

## Adding support for another brand

The domain and the use cases do not know Samsung exists. Supporting another brand means writing new adapters for the ports in `dominio/puertos.py` (probe, waker, key channel, speakers, app launcher, scanner) and choosing them in `composicion.py`. Model-specific timing lives in `dominio/presencia.py`.
