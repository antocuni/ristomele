# Bluetooth Testing — Minimal Reproducer on Laptop

## Goal

Verify that a browser page served over HTTPS with a self-signed certificate
can access `navigator.bluetooth` (Web Bluetooth API). No printer or Raspberry
Pi needed — just a laptop with Chrome and Bluetooth hardware.

---

## Step 1 — Generate a self-signed certificate

```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem \
    -days 365 -nodes -subj "/CN=localhost"
```

---

## Step 2 — Minimal Flask app

Create `test_https.py` alongside the certs:

```python
from flask import Flask, send_file
app = Flask(__name__)

@app.route('/')
def index():
    return send_file('web.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))
```

Copy (or symlink) `printer-web/web.html` into the same directory, then:

```bash
pip install flask
python test_https.py
```

---

## Step 3 — Open in Chrome

Navigate to `https://localhost:5000/`.

Chrome will show "Your connection is not private". Click:
**Advanced → Proceed to localhost (unsafe)**

The page should load. Open the browser console and run:

```js
console.log(typeof navigator.bluetooth)
```

- `"object"` → Web Bluetooth is available. HTTPS bypass works. ✅
- `"undefined"` → secure context not granted after bypass. ✗

---

## Step 4 — Test the BLE scan (optional, requires Bluetooth hardware)

Click "Connect & Print" in the loaded page. Chrome should show the OS
Bluetooth device picker. You do not need a printer — just seeing the picker
appear confirms that `navigator.bluetooth.requestDevice()` is callable.

If no Bluetooth devices are nearby the picker will show an empty list or a
"no devices found" message; that is still a pass.

---

## Pass criteria

| Check | Expected |
|-------|----------|
| Page loads after "proceed anyway" | Yes |
| `typeof navigator.bluetooth` in console | `"object"` |
| `requestDevice()` shows OS picker (if BT hardware present) | Yes |

If all three pass, the self-signed-cert approach is confirmed and the
HTTPS section of `offline-usage.md` is validated.
