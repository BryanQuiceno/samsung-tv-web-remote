# Troubleshooting

First check, always: **can the server see the TV?**

```bash
curl -s http://<tv-ip>:8001/api/v2/ | head -c 300
```

JSON back means the TV is on the network and reachable. Nothing back means it is off, unplugged, on another network, or at another address.

## The scanner does not find my TV

- **It must be switched on.** A TV that is off does not answer the scan.
- **Same subnet.** The server scans its own subnet only (up to a /22). A TV on a guest Wi-Fi or another VLAN is invisible, and Wake-on-LAN would not reach it anyway.
- **Client isolation.** Some routers isolate Wi-Fi clients from each other ("AP isolation"). Disable it for that network.
- **It is not a Samsung Tizen TV**, or it is a pre-2016 model. The `curl` above settles it.
- You can always add it by address: *No aparece en la lista* in the UI, or `mando anadir <ip> <name>`.

## The pairing prompt never appears, or pairing fails

- The TV must be **on**, showing a picture, not in standby.
- On the TV: *Settings → General → External Device Manager → Device Connection Manager*. *Access Notification* must not be "Off", and the server must not be in the denied list (*Device List*). Menu names vary by year.
- If it was denied once, remove the entry from that device list and ask again (*Pedirle permiso* in the TV's settings, or `mando --tv <id> emparejar`).
- The server waits 45 seconds. Ask again if you were late.

## It reports the state but does not obey

It is not paired: the UI shows *"Este televisor aún no ha dado permiso"*. Pair it. If it was paired before, the TV may have forgotten the device (factory reset, cleared device list): delete `datos/televisores/<id>/token.txt` and pair again.

## It does not turn on

Power-on is Wake-on-LAN followed by a key press.

- Enable *Power On with Mobile* (or similar) in the TV's network settings.
- A TV on **Wi-Fi** often cannot be woken once it has been off for a while; **cable** is reliable.
- The server must be on the same subnet (the magic packet is a broadcast).
- If the server has several network interfaces, the packet is bound to the LAN one automatically. `GET /api/televisores/<id>/ajustes` shows which address it is using (`servidor.ip`).
- The message *"No contesta al Wake-on-LAN"* means port 8001 never came up within 90 s: it is a network problem, not a key problem.
- The message *"Se cayó de la red tras la tecla dos veces"* means the network woke but the screen did not stay on, twice.

## It says "Apagada" but the TV is on

Most likely its IP changed. The watcher corrects this within a minute — if the watcher is installed (`crontab -l`). To force it: *Ajustes → Buscarla en la red*, or `mando buscar`. Reserving the TV's address in your router's DHCP avoids the gap.

## It says "Sin confirmar" (unsure)

Expected right after the TV appears on the network: an off TV also answers for a while. It becomes "Encendida" after 3 minutes of continuous answers. If it stays unsure forever, the watcher is not running.

## Volume buttons are greyed out

Audio is only reachable while the TV is awake, and the audio port comes up a few seconds after the rest.

## The mute icon flickers on the TV

Every audio command draws the icon on screen. Do not loop volume or mute commands from scripts.

## Everything broke after moving the server

The pairing token is tied to the TV, not to the server's IP: copying `datos/` to the new machine keeps the pairing. If you use a local DNS name, update the rewrite to the new server address.
