# The Samsung local protocol, as used here

Samsung does not document local network control of its TVs. What follows is the community-known protocol, written down as this project uses it and as it was observed on a **Samsung UE40NU7115** (model code `18_KANTSU_UHD_BASIC`, Tizen, wired). The only official API is the SmartThings cloud, which this project deliberately does not use.

Each function lives on a different port and has its own preconditions:

| Function | Transport | Port | Needs |
|---|---|---|---|
| Is it there? / device info | HTTP REST | 8001 | nothing |
| Remote keys, power off | Secure WebSocket | 8002 | pairing token |
| Power on | Wake-on-LAN (UDP broadcast) | 9 and 7 | the TV's MAC |
| Volume and mute | UPnP SOAP `RenderingControl` | 9197 | TV awake |
| Launch apps / deep links | DIAL (HTTP) | 8080 | TV awake |

Code: [`servidor/mando_del_televisor/infraestructura/samsung/`](../servidor/mando_del_televisor/infraestructura/samsung/).

## Device info — REST, port 8001

```
GET http://<tv>:8001/api/v2/
```

No authentication. Returns JSON; the useful part is `device`:

```json
{
  "device": {
    "type": "Samsung SmartTV",
    "name": "[TV] Living room",
    "modelName": "UE40NU7115",
    "model": "18_KANTSU_UHD_BASIC",
    "OS": "Tizen",
    "networkType": "wired",
    "wifiMac": "aa:bb:cc:dd:ee:ff",
    "TokenAuthSupport": "true",
    "FrameTVSupport": "false"
  }
}
```

How this project uses it:

- **Probe.** It is a passive query: it does not wake a sleeping TV. Opening the WebSocket on 8002 also "answers", but it *does* wake the TV, which would corrupt the presence measurement. That is why the probe is REST and nothing else.
- **Discovery.** The scanner opens port 8001 on every address of the server's subnet in parallel and keeps the ones whose `type` contains `Samsung`. `TokenAuthSupport: "true"` marks a TV this project can pair with.
- **Power state, when available.** Newer models add `"PowerState": "on" | "standby"`. The UE40NU7115 does **not** have this field. When it is present the TV's own answer is trusted; when absent, the state is inferred (see the README).
- **MAC address.** `wifiMac` is not trusted for Wake-on-LAN: a wired TV must be woken through its wired MAC. The MAC is taken from the system neighbour table (`ip neigh`) after pinging the TV, which is by definition the MAC of the interface in use.

## Remote keys — WebSocket, port 8002

```
wss://<tv>:8002/api/v2/channels/samsung.remote.control?name=<base64 app name>&token=<token>
```

The TV uses a self-signed certificate. This project delegates this channel to the [`samsungtvws`](https://github.com/xchwarze/samsung-tv-ws-api) library.

**Pairing.** The first connection without a token makes the TV show an *Allow / Deny* prompt. Someone has to accept it with the TV's physical remote. The TV then sends a token in the `ms.channel.connect` event, which is saved (one `token.txt` per TV) and reused forever. There is no way to pair remotely. Connecting with a valid token shows nothing on screen.

**Sending a key:**

```json
{
  "method": "ms.remote.control",
  "params": { "Cmd": "Click", "DataOfCmd": "KEY_VOLUP", "Option": "false", "TypeOfRemote": "SendRemoteKey" }
}
```

Keys used: `KEY_POWER`, `KEY_POWERON`, `KEY_HOME`, `KEY_SOURCE`, `KEY_RETURN`, `KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT`, `KEY_ENTER`, `KEY_INFO`, `KEY_CHUP`, `KEY_CHDOWN`, `KEY_PLAY`, `KEY_PAUSE`.

## Power on — Wake-on-LAN

A standard magic packet (6 × `0xFF` followed by the MAC 16 times) sent as UDP broadcast to ports 9 and 7, both to the subnet broadcast address and to `255.255.255.255`.

Two things matter in practice:

- **Bind the socket to the LAN address of the server.** On a host with several interfaces (Docker bridges, VPNs) an unbound broadcast leaves through the wrong one and power-on fails intermittently. The LAN address is looked up from the routing table on every call.
- **The packet is addressed to the MAC, not the IP.** It wakes the TV even if its IP has changed.

Wake-on-LAN only wakes the **network card**. The screen stays dark until a key arrives, hence the next step.

## The power-on sequence

1. Send the magic packet; repeat every few seconds until port 8001 answers (up to 90 s).
2. Send `KEY_POWERON` over the WebSocket.
3. **Verify**: keep probing for ~130 s. A TV that is really on never drops; one that swallowed the key drops off the network within two minutes.
4. If it dropped, run the whole sequence once more.
5. Un-mute (see quirks).

Step 2 is lost now and then — the TV is half awake and ignores the key. That was the classic "sometimes it does not turn on", and it is the reason steps 3 and 4 exist.

## Volume and mute — UPnP, port 9197

```
POST http://<tv>:9197/upnp/control/RenderingControl1
Content-Type: text/xml; charset="utf-8"
SOAPACTION: "urn:schemas-upnp-org:service:RenderingControl:1#SetVolume"

<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
            s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>
<u:SetVolume xmlns:u="urn:schemas-upnp-org:service:RenderingControl:1">
  <InstanceID>0</InstanceID><Channel>Master</Channel><DesiredVolume>15</DesiredVolume>
</u:SetVolume></s:Body></s:Envelope>
```

Actions used: `GetVolume` (reply has `<CurrentVolume>`), `SetVolume`, `GetMute` (`<CurrentMute>`), `SetMute` (`<DesiredMute>0|1</DesiredMute>`). Volume is absolute, 0–100, which is why this channel is used instead of repeating `KEY_VOLUP`.

The port only answers while the TV is awake, and comes up a few seconds later than the rest after power-on. No authentication.

## Apps and deep links — DIAL, port 8080

```
GET  http://<tv>:8080/ws/app/Netflix          -> XML; contains <state>running</state> when open
POST http://<tv>:8080/ws/app/Netflix          -> opens Netflix
POST http://<tv>:8080/ws/app/Netflix          -> opens Netflix on a title
Content-Type: text/plain; charset=utf-8

v=80057281
```

The number is the title id from its URL, `netflix.com/title/`**`80057281`**. Deep-linking is far more robust than navigating menus with arrow keys, which breaks whenever the app changes its home screen. Choosing a profile cannot be done this way. Specification: <http://www.dial-multiscreen.org/>.

## Quirks of the UE40NU7115

Measured on the real set. Other models may differ.

- **`KEY_POWEROFF` does nothing.** The key that turns it off is `KEY_POWER`. A tell-tale sign of using the wrong one: the following "power on" finishes in 1–2 s, because the TV was never off.
- **No power state anywhere.** REST, SOAP, DLNA, SSDP and the WebSocket all answer identically with the screen on or off.
- **It lingers on the network when off**: ~90 s after power-off, and again whenever something pokes it, but never more than ~2 minutes at a stretch.
- **It always comes back muted** after a network power-on. One `SetMute 0` fixes it. Send it **once**: every audio command draws the volume/mute icon on screen, and looping them looks like a flickering bug from the sofa.
- **The active input is not exposed.** `KEY_SOURCE` can only be sent blind.
- **It advertises itself as a DLNA renderer**, so pushing media to it is possible (not implemented here).
- **Its IP changes** unless reserved in the router. This project identifies the TV by MAC and follows it; a DHCP reservation is still a good idea.
