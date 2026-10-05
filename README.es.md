# Mando web para televisores Samsung

**Un mando a distancia web, alojado en casa, para televisores Samsung Smart TV (Tizen), que funciona por la red local: sin nube, sin cuenta de SmartThings y sin instalar ninguna app.** Se abre en el móvil y enciende, apaga, cambia el volumen, pulsa teclas y abre Netflix en un título concreto.

Hecho y probado sobre un **Samsung UE40NU7115** (serie NU7100, 2018). Lleva **varios televisores**, los encuentra solo en la red y sigue funcionando cuando el router le cambia la dirección a uno.

> 🇬🇧 English: [README.md](README.md). La documentación detallada (`docs/`) está en inglés; el código, los comentarios y la interfaz están en español.

<p>
  <img src="docs/img/remote.png" width="250" alt="El mando: pestañas de televisores, estado, encendido y volumen">
  <img src="docs/img/add-tv-found.png" width="250" alt="Añadir televisor: los Samsung encontrados en la red">
  <img src="docs/img/second-tv-settings.png" width="250" alt="Ajustes de un televisor: permiso, dirección, quitar">
</p>

## Qué hace

- **Enciende** con Wake-on-LAN más la tecla de encendido, y **comprueba que la pantalla se quedó encendida** antes de decirlo (reintenta una vez si la tecla se perdió).
- **Apaga**, **volumen**, **silencio**, **cruceta y teclas habituales**.
- **No miente sobre si está encendido.** Los Samsung antiguos no dicen si la pantalla está encendida y siguen contestando en la red un rato después de apagarse. Aquí se mide *cuánto lleva contestando* en vez de fiarse de una respuesta suelta.
- **Añadir un televisor desde la web**: busca los Samsung de la red, eliges el tuyo, le pones nombre y aceptas el aviso en su pantalla.
- **Aguanta los cambios de dirección.** El televisor se identifica por su MAC. Si el router lo mueve, un vigía lo encuentra en un minuto.
- **Netflix en un título concreto**, por DIAL.
- **Línea de comandos** con el mismo motor que la web: para cron, scripts y agentes de IA.
- **Solo red local.** Nada sale de casa.

## Televisores compatibles

| Televisor | Estado |
|---|---|
| **Samsung UE40NU7115** (serie NU7100, 2018, por cable) | Probado a fondo. Las reglas de tiempos están medidas en este aparato. |
| Otros Samsung Tizen de 2016 en adelante | Deberían funcionar: mismo protocolo. Sin verificar en aparato real. |
| Modelos modernos que publican `PowerState` (≈2020+) | Soportados en código y pruebas. **Sin verificar en aparato real.** |
| Samsung anteriores a 2016 | No compatibles. El buscador los marca. |
| LG, Sony, Android TV… | No. Solo Samsung. |

## Puesta en marcha

Hace falta una máquina Linux siempre encendida **en la misma red que el televisor**, con Python 3.10+ y Node.js 22+ (Node solo para compilar la web una vez).

```bash
git clone https://github.com/BryanQuiceno/samsung-tv-web-remote.git
cd samsung-tv-web-remote

python3 -m venv .venv
.venv/bin/pip install -r servidor/requirements.txt
(cd web && npm ci && npm run build)

.venv/bin/python servidor/servir.py        # http://<esta-maquina>:8099
```

Al abrirlo sin ningún televisor, va directo a **Añadir televisor**:

1. Enciende el televisor. La página lista los Samsung que encuentra (unos 3 segundos).
2. Toca el tuyo y ponle nombre (el de la habitación).
3. Mira el televisor: sale un aviso. Elige **Permitir** con su mando. Tiene que hacerlo alguien delante, una vez por televisor.

Y el **vigía** en el cron, que es lo que hace fiable el estado y lo que sigue al televisor si cambia de dirección:

```cron
* * * * * cd /ruta/a/samsung-tv-web-remote/servidor && ../.venv/bin/python vigia.py >/dev/null 2>&1
```

Instalación permanente (servicio, proxy, nombre local): [docs/deployment.md](docs/deployment.md).

## Línea de comandos

```bash
mando() { /ruta/.venv/bin/python /ruta/servidor/mando.py "$@"; }

mando televisores                  # los que hay
mando descubrir                    # los Samsung que se ven ahora en la red
mando anadir 192.168.1.50 Dormitorio

mando estado                       # apagada | encendida | dudosa
mando on        ;  mando off
mando vol 15    ;  mando vol +2    ;  mando vol
mando mute on   ;  mando mute off
mando tecla INICIO                 # `mando teclas` las lista
mando netflix https://www.netflix.com/title/80057281
mando buscar                       # volver a encontrarlo por la MAC
mando --tv dormitorio on           # con varios: elegir cuál
```

## Cómo sabe si está encendido

En el UE40NU7115 nada en la red dice si la pantalla está encendida. Medido sobre el aparato:

| Situación | Qué hace en la red |
|---|---|
| Encendido | Responde siempre, sin un solo hueco |
| Apagado | Responde ~90 s tras apagarse y vuelve si algo lo estimula, pero **nunca más de ~2 min seguidos** |

Lo único que un televisor apagado no puede fingir es la **constancia**. El vigía anota cada minuto si contesta, y el estado sale de cuánto dura la racha: **apagada** (no contesta), **encendida** (más de 3 minutos contestando, o un encendido recién verificado) o **sin confirmar** (acaba de aparecer).

Los modelos que publican `PowerState` no necesitan nada de esto: se les cree.

## Documentación (en inglés)

- [docs/samsung-local-protocol.md](docs/samsung-local-protocol.md) — el protocolo de red: puertos, peticiones, emparejamiento y las manías del UE40NU7115.
- [docs/http-api.md](docs/http-api.md) — la API HTTP.
- [docs/deployment.md](docs/deployment.md) — servicio, vigía, proxy, variables y carpeta de datos.
- [docs/architecture.md](docs/architecture.md) — cómo está organizado el código, con glosario español → inglés.
- [docs/troubleshooting.md](docs/troubleshooting.md) — no lo encuentra, no enciende, no obedece…

## Límites

- **Sin contraseña.** Cualquiera en tu red que llegue a la página maneja los televisores. No lo expongas a internet.
- **El buscador solo ve televisores encendidos** y en la misma red que el servidor.
- **Samsung no documenta este protocolo.** Es el que conoce la comunidad, estable desde hace años, pero una actualización de firmware podría cambiarlo.
- **Al encender se quita el silencio en todos los televisores.** Es una manía del UE40NU7115, que vuelve siempre silenciado.
- Elegir perfil de Netflix no se puede por red.

## Licencia

MIT — ver [LICENSE](LICENSE). Sin relación con Samsung.
