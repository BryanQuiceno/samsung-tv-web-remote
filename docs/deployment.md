# Deployment

A permanent install has three parts: the **server** (web UI + API), the **watcher** (a cron job) and, optionally, a **reverse proxy** to reach it by name on port 80. Ready-to-edit files are in [`despliegue/`](../despliegue/).

The examples assume the repository is in `/opt/samsung-tv-web-remote`, with the virtualenv in `.venv` inside it, running as user `tv`. Adjust to taste.

## 1. Install

```bash
git clone https://github.com/BryanQuiceno/samsung-tv-web-remote.git /opt/samsung-tv-web-remote
cd /opt/samsung-tv-web-remote
python3 -m venv .venv
.venv/bin/pip install -r servidor/requirements.txt
(cd web && npm ci && npm run build)
```

The server must be on the **same subnet as the TVs**: Wake-on-LAN and the neighbour-table lookup do not cross routers. It needs the `ip` (iproute2) and `ping` commands, as an ordinary user.

## 2. The server as a systemd service

Edit the user and paths in [`despliegue/mando-tv.service`](../despliegue/mando-tv.service), then:

```bash
sudo cp despliegue/mando-tv.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mando-tv
journalctl -u mando-tv -f
```

## 3. The watcher in cron — not optional

`crontab -e` as the same user:

```cron
* * * * * cd /opt/samsung-tv-web-remote/servidor && ../.venv/bin/python vigia.py >/dev/null 2>&1
```

Every minute it records, for each TV, whether it answers. Without it:

- the power state of TVs that do not report it (UE40NU7115) is never certain, and
- a TV whose IP changed is not found again automatically.

It never wakes a TV. When a TV does not answer it looks for its MAC in the neighbour table, and sweeps the subnet at most once every ten minutes.

## 4. Reverse proxy and a friendly name (optional)

[`despliegue/Caddyfile`](../despliegue/Caddyfile) is a minimal [Caddy](https://caddyserver.com/) config that serves the remote at `http://mando.casa` and, as a fallback that needs no DNS, on port 8080. With a proxy in front, keep the server on loopback (`MANDO_HOST=127.0.0.1`, as in the sample unit).

For the name to resolve, add a DNS rewrite in whatever resolves names in your LAN (AdGuard Home, Pi-hole, your router): `mando.casa → <server IP>`.

> Do not use a `.dev` or `.app` name for this. Those TLDs are on the browser HSTS preload list: the browser forces HTTPS and will not let you click through a certificate warning. Use `.lan`, `.home.arpa`, `.casa`…

## Environment variables

| Variable | Default | |
|---|---|---|
| `MANDO_HOST` | `0.0.0.0` | Address the server listens on |
| `MANDO_PUERTO` | `8099` | Port |
| `MANDO_DATOS` | `servidor/datos` | Data folder (see below). Must be the same for the server, the watcher and the CLI. |

## The data folder

Everything the program remembers is plain text under `servidor/datos/`, which is git-ignored. No database.

```
datos/
  televisores/
    salon/                 one folder per TV; the folder name is its id
      televisor.json       who it is: name, model, MAC
      ajustes.json         where it is today: IP, how it was learned, previous IP
      token.txt            the pairing token (treat it as a secret)
      estado.json          the watcher's current streak
      historial.jsonl      one sample per line, last 24 h
  quitados/                removed TVs are moved here, never deleted
  netflix.json             optional: { "stranger things": "80057281" }
```

**Backup**: copy `datos/`. Restoring it restores the TVs and their pairing, so nobody has to accept the prompt again.

`netflix.json` maps names of your choice to Netflix title ids, so `mando netflix "stranger things"` works instead of pasting the URL.

## Updating

```bash
cd /opt/samsung-tv-web-remote && git pull
.venv/bin/pip install -r servidor/requirements.txt
(cd web && npm ci && npm run build)      # only if web/ changed
sudo systemctl restart mando-tv          # only if servidor/ changed
```

## Tests

```bash
cd servidor && ../.venv/bin/python -m unittest discover pruebas
```

They run against test doubles: no network, no TV, no waiting.
