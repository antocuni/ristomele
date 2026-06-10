# Offline Usage — Making Android/iOS Happy on a Local WiFi

## Problem

Modern mobile OSes detect internet connectivity by probing well-known URLs:

| OS | Probe URL | Expected response |
|----|-----------|-------------------|
| Android | `connectivitycheck.gstatic.com/generate_204` | HTTP 204 No Content |
| iOS / macOS | `captive.apple.com/hotspot-detect.html` | HTTP 200 with specific body |
| Windows | `www.msftconnecttest.com/connecttest.txt` | HTTP 200 "Microsoft Connect Test" |

When the local WiFi has no internet access (festival/sagra scenario), these
probes fail. Consequences:

- Android silently switches traffic to mobile data; the browser cannot reach
  the Flask server.
- iOS shows a "No Internet Connection" warning and may prefer cellular.
- Some Android versions refuse to use the WiFi at all for background requests.

## Solution: Fake Connectivity on the Raspberry Pi

Configure the Pi to respond to connectivity probes so all devices believe
there is internet. No per-device setup needed.

### Step 1 — DNS: redirect probe hostnames to the Pi

Add to `/etc/dnsmasq.conf` (or the local dnsmasq config):

```
address=/connectivitycheck.gstatic.com/<PI_IP>
address=/connectivitycheck.android.com/<PI_IP>
address=/www.gstatic.com/<PI_IP>
address=/captive.apple.com/<PI_IP>
address=/www.apple.com/<PI_IP>
address=/www.msftconnecttest.com/<PI_IP>
address=/www.msftncsi.com/<PI_IP>
```

Replace `<PI_IP>` with the Pi's static LAN IP (e.g. `192.168.1.6`).

Restart dnsmasq: `sudo systemctl restart dnsmasq`

This only works if the Pi (or the router it controls) is the DHCP DNS server
for the local network — which is the typical setup when the Pi acts as the AP
or DHCP server.

### Step 2 — Flask: respond to probe requests

Add these routes to the Flask app (`server/ristomele.py` or `server/app.py`):

```python
@app.route('/generate_204')
def generate_204():
    """Android connectivity check."""
    return '', 204

@app.route('/hotspot-detect.html')
def hotspot_detect():
    """iOS / macOS connectivity check."""
    return '<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>', 200

@app.route('/connecttest.txt')
def connecttest():
    """Windows connectivity check."""
    return 'Microsoft Connect Test', 200
```

Flask listens on port 5000, but connectivity probes go to port 80. Two options:

**Option A1 (simplest)** — use nginx or a second minimal HTTP server on port
80 that serves just these three responses, and proxy everything else to
Flask on 5000.

**Option A2** — configure the Pi's firewall to redirect port 80 → 5000:

```
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 5000
sudo iptables-save > /etc/iptables/rules.v4
```

Option A2 is simpler to maintain (no additional process), but means port 80
is effectively an alias for the Flask app — which is fine in this closed
network.

### Step 3 — Verify

1. Connect an Android phone to the local WiFi.
2. Check the WiFi settings: the network should show no "!" warning and no
   "No internet" label.
3. Open a browser and navigate to `http://<PI_IP>:5000/` — it should load.

## HTTPS Setup (required for Web Bluetooth)

Web Bluetooth requires a secure context. The Flask server must be reachable
over HTTPS. A self-signed certificate is sufficient — Chrome shows a one-time
warning that the user dismisses once per device.

```bash
# Generate a self-signed cert (valid 10 years)
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem \
    -days 3650 -nodes -subj "/CN=ristomele"
```

Then pass the cert to Flask/uwsgi. With uwsgi:

```ini
# in ristomele.ini (uwsgi config)
https = 0.0.0.0:5000,/path/to/cert.pem,/path/to/key.pem
```

Or if using nginx as a front-end, configure the SSL there and proxy to Flask
on a local port.

Users navigate to `https://<PI_IP>:5000/`, click "Advanced → Proceed to
<PI_IP> (unsafe)" once, and thereafter the browser considers the origin
secure for the rest of the session (and future visits if the cert doesn't
change).

## Notes

- This setup is harmless on a closed LAN; it does not affect internet routing.
- If the WiFi router (not the Pi) is the DHCP/DNS server, the dnsmasq entries
  must go there instead (or the router must forward DNS to the Pi).
- iOS also checks certificate validity for some probes. Since we serve plain
  HTTP, use the `hotspot-detect.html` path which works without HTTPS.
- The fix is idempotent — it can be left in place permanently; it causes no
  problems when the Pi is connected to real internet.
