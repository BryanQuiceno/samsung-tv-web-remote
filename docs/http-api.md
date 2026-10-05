# HTTP API

The web UI talks to the server through this API, and anything else can too. JSON in, JSON out. Interactive docs are served at `/api/docs` (FastAPI/Swagger).

**There is no authentication.** Keep the server on your LAN.

Errors use standard status codes with a human-readable message (in Spanish) in `detail`:

| Code | Meaning |
|---|---|
| 400 | Bad input (not an IP address, unknown key, no Samsung TV at that address) |
| 404 | No TV with that id |
| 409 | Not possible right now (TV is off, an operation is already running, TV already added, the address belongs to another device) |
| 502 | The TV did not accept the command (often: not paired) |

## TVs

### `GET /api/televisores`
The configured TVs.
```json
{ "televisores": [ { "id": "salon", "nombre": "Salón", "modelo": "UE40NU7115", "ip": "192.168.1.128", "emparejado": true } ] }
```
`emparejado` = paired: someone accepted the prompt on the TV. An unpaired TV reports its state but does not obey.

### `POST /api/televisores/buscar`
Scans the LAN for Samsung TVs that are switched on. Takes ~3 s.
```json
{ "hallados": [ { "ip": "192.168.1.128", "nombre": "Living room", "modelo": "UE40NU7115", "compatible": true, "yaAnadido": "Salón" } ] }
```
`yaAnadido` is the name of the configured TV with the same MAC, or `null`.

### `POST /api/televisores` → 201
Adds the TV found at an address. Body: `{ "ip": "192.168.1.50", "nombre": "Bedroom" }` (`nombre` optional; defaults to the TV's own name). The id is derived from the name (`bedroom`). The TV still needs pairing.

### `POST /api/televisores/{id}/emparejar`
Asks the TV for permission and **blocks up to 45 s** while someone accepts the prompt on its screen.
```json
{ "emparejado": true, "mensaje": "Permiso concedido. Ya se puede manejar." }
```

### `DELETE /api/televisores/{id}`
Removes a TV. Its data folder is moved to `datos/quitados/`, not deleted.

## One TV

All under `/api/televisores/{id}`.

### `GET /estado`
```json
{
  "estado": "encendida",
  "esCerteza": true,
  "segundosEnEsteEstado": 217,
  "segundosParaFiarse": 180,
  "sonido": { "volumen": 16, "silenciado": false },
  "confirmada": false,
  "operacion": null,
  "televisor": { "id": "salon", "nombre": "Salón", "modelo": "UE40NU7115", "ip": "192.168.1.128", "emparejado": true }
}
```
- `estado`: `apagada` (off), `encendida` (on) or `dudosa` (unsure: it has just appeared on the network).
- `sonido` is `null` when the TV is off.
- `operacion`: the long-running operation, if any — `{ nombre, mensaje, progreso (0–1), terminada, exito }`. Poll this endpoint to follow a power-on.

### `GET /presencia`
The watcher's samples for the last 90 minutes: `{ "muestras": [ { "t": 1791221641, "responde": true } ] }`.

### `POST /encender`
Starts the power-on sequence in the background and returns the operation immediately. It takes from a couple of minutes (the verification alone is ~130 s) up to several if a retry is needed; follow it through `GET /estado`. `409` if one is already running.

### `POST /apagar`
`{ "mensaje": "Apagada", "yaEstabaApagada": false }`

### `POST /confirmar`
Resolves a `dudosa` state by watching the TV for ~2 minutes (background operation, like power-on).

### `POST /volumen`
Body: `{ "volumen": 15 }` (absolute, 0–100) or `{ "paso": 1 }` / `{ "paso": -1 }` (relative). Returns `{ "volumen": 15, "silenciado": false }`.

### `POST /silencio`
Body: `{ "silenciado": true }`, `{ "silenciado": false }`, or `{}` to toggle.

### `POST /tecla`
Body: `{ "tecla": "INICIO" }`. Names: `APAGAR`, `ENCENDER`, `INICIO` (Home), `FUENTE` (Source), `VOLVER` (Back), `ARRIBA`, `ABAJO`, `IZQUIERDA`, `DERECHA`, `ACEPTAR` (OK), `INFO`, `CANAL_MAS`, `CANAL_MENOS`, `REPRODUCIR` (Play), `PAUSA`. `GET /api/teclas` lists them.

### `POST /netflix`
Body: `{ "titulo": "https://www.netflix.com/title/80057281" }` — a Netflix URL, a bare title id, or a name saved in `datos/netflix.json`. `{}` just opens Netflix.

### `GET /ajustes`
Where the server believes the TV is and how it learned it.
```json
{
  "televisor": { "ip": "192.168.1.128", "mac": "AA:BB:CC:DD:EE:FF", "origen": "encontrada", "desde": 1791212879.3, "anterior": "192.168.1.146", "emparejado": true },
  "servidor": { "ip": "192.168.1.10", "interfaz": "eth0" }
}
```
`origen`: `al_anadirlo` (set when added), `a_mano` (typed by hand), `encontrada` (the server found it by MAC after it moved).

### `POST /ajustes/buscar`
Sends a Wake-on-LAN, sweeps the subnet and looks for the TV's MAC. Updates the address if it moved. ~5 s. The reply adds `resultado: { encontrada, cambiada, mensaje }`.

### `POST /ajustes/direccion`
Body: `{ "ip": "192.168.1.128" }`. Sets the address by hand. Rejected with `409` if a different device answers there.

## Examples

```bash
B=http://192.168.1.10:8099/api/televisores/salon
curl -s $B/estado | jq .estado
curl -s -X POST $B/encender
curl -s -X POST $B/volumen -H 'Content-Type: application/json' -d '{"volumen": 12}'
curl -s -X POST $B/tecla   -H 'Content-Type: application/json' -d '{"tecla": "INICIO"}'
```
