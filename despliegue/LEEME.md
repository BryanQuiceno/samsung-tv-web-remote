# Deployment files

Templates for a permanent install. **Editing them here changes nothing**: they have to be copied to the system. Full walkthrough in [docs/deployment.md](../docs/deployment.md).

| File | Goes to | Then |
|---|---|---|
| `mando-tv.service` | `/etc/systemd/system/` | `systemctl daemon-reload && systemctl enable --now mando-tv` |
| `caddy.service` | `/etc/systemd/system/` | same, with `caddy` (only if Caddy was installed as a bare binary) |
| `Caddyfile` | `/etc/caddy/` | `systemctl restart caddy` |

Caddy does not hot-reload here: its admin API is switched off on purpose, so `reload` restarts (already set in the unit).

Do not forget the watcher in cron — see the deployment guide.
