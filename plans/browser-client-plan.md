# Browser Client — Migration Plan

## Goal

Replace the Kivy-based mobile client with a browser-based client that:

- Runs on any device with a modern browser (Android, iOS, desktop)
- Talks to the **existing Flask server unchanged**
- Covers all current client functionality
- Is easy to deploy (just files served from the existing Flask server)

One small server addition is required: a `GET /menu/` endpoint that exposes
the active menu and mode config (see Menu Handling). All other REST API
endpoints already exist and work correctly (see `system-overview.md`).

---

## Hard Constraint: No Internet Access

The entire system operates on a **closed local WiFi network with no internet
access**. This is a hard requirement, not an edge case. Consequences:

- **All assets must be served locally** from the Flask server. No CDN links
  for Bootstrap, fonts, icons, or anything else. Every external resource
  referenced in `index.html` must be vendored into `server/static/client/`.
- **Android and iOS detect "no internet"** and may silently route traffic over
  mobile data, making the Flask server unreachable. This must be fixed at the
  network/server level before the browser client can work reliably. See
  `offline-usage.md` for the solution (fake connectivity probes on the Pi).
- Import maps and ES module CDN imports (`esm.sh`, `unpkg.com`, `skypack.dev`)
  are not usable. Any JS framework must be bundled locally.

---

## Recommended Technology Stack

| Concern | Choice | Rationale |
|---------|--------|-----------|
| UI framework | **Vanilla JS + minimal CSS** | The UI is simple enough that a framework is optional; avoiding build toolchains reduces ops complexity on the Raspberry Pi |
| Styling | Bootstrap 5 (**vendored locally**) | Already partially used (stats.html); provides mobile-first responsive layout. Must be downloaded and served from Flask, not from a CDN. |
| HTTP client | `fetch` API | Native, no deps |
| Build toolchain | None (single `index.html` + one `.js` file) | Deployable by copying files; no npm, no bundler |
| Local storage | `localStorage` | Persist `cashier`, `columns` |

If the UI grows complex enough to warrant a framework, **Preact** (3kB, same
API as React) can be used — but its `.js` file must be vendored locally, not
loaded via a CDN import map.

---

## What the Browser Client Must Do

Derived from the current Kivy client (see `system-overview.md`):

1. **Settings**: let the user configure cashier name, display columns, and
   BLE printer (via `navigator.bluetooth.requestDevice()`); save to
   `localStorage`. Server host:port and mode (`is_sagra`/`is_croce`) are not
   client concerns — the origin is implicit (app is served by Flask), and the
   mode is read from the server (see Menu Handling).

2. **Main screen**: buttons for "Nuovo ordine" (sagra/croce) or "Mappa
   tavoli" (ristorante), "Lista ordini", "Configura tavoli", "Opzioni".

3. **Tables screen** (ristorante only): grid of tables (rows×cols); each
   cell shows table number + waiter name; tap to start a new order for that
   table.

4. **Edit tables screen**: same grid but tapping a cell fills a text input
   with the waiter name so it can be edited; "Salva" sends `PUT /tables/`.

5. **New order screen**: scrollable list of menu items with `[−]` count
   `[+]` buttons, section separators, customer name + notes inputs. "OK"
   → show order summary.

6. **Show order screen**: monospaced receipt preview, total, cash calculator
   (received → change), "Salva"/"Cibo", "Bar", "Indietro" buttons.

7. **Order list screen**: reverse-chronological list of past orders; tap to
   view / reprint.

8. **Print**: the server handles kitchen/bar printing via `POST
   /orders/<id>/print/` and `POST /orders/<id>/print_drinks/`. The client
   also prints a local customer receipt to a BLE thermal printer via the
   Web Bluetooth API (Chrome/Android only; gracefully disabled on
   unsupported browsers).

---

## Screens and Routes

A simple client-side router (hash-based, no server involvement) maps URLs to
views:

```
#/               → MainScreen
#/tables         → TablesScreen
#/tables/edit    → EditTablesScreen
#/order/new?table=<name>&waiter=<name>  → NewOrderScreen
#/order/<id>     → ShowOrderScreen (existing order)
#/order/preview  → ShowOrderScreen (unsaved, data in sessionStorage)
#/orders         → OrderListScreen
#/settings       → SettingsScreen
```

---

## Menu Handling

The menu is hardcoded in `mobile/src/ristomele/menu.py`. The server will
expose it via a new endpoint so the browser client has a single source of
truth and no mode config of its own.

### `GET /menu/` (new endpoint)

Returns the active menu **and** the server's mode config:

```json
{
  "is_sagra": false,
  "is_croce": false,
  "items": [
    {"kind": "separator", "name": "Primi",            "price": 0,   "is_drink": false},
    {"kind": "item",      "name": "Trenette al pesto","price": 6.5, "is_drink": false},
    ...
  ]
}
```

The client calls this once on startup and caches the result in
`sessionStorage`. It uses `is_sagra`/`is_croce` to decide which screens and
UI elements to show (e.g. hide the tables map in sagra mode, show Fila A/B
indicator). The menu `items` array is used as-is for the NewOrderScreen.

Implementation on the server: read `get_menu()` from `menu.py` and
`server/config.py:MODE` and serialise both into the response. No database
involvement.

> **Note**: when `GET /menu/` is added, update the Kivy client to fetch
> the menu from the server instead of importing `menu.py` directly. The
> Kivy app must remain fully functional alongside the browser client, so
> the two should share the same source of truth from that point on.

---

## Implementation Plan

### Phase 1 — Minimal viable client (sagra mode)

Implement just the sagra workflow (no tables, no waiters):

1. `SettingsScreen`: cashier name, display columns, and BLE printer
   selection ("Seleziona stampante" → `navigator.bluetooth.requestDevice()`),
   saved to `localStorage`. No server address, no mode — both resolved
   server-side. Includes a **"Sincronizza ora"** button that reads the
   browser's clock and calls `POST /timestamp/` to set the server time.
   This is a hard operational requirement: the Raspberry Pi has no
   persistent RTC, so after every reboot an admin must set the time before
   taking any orders (otherwise `date_dwim` and order timestamps are wrong).
   The button should display the current server time (via `GET /timestamp/`)
   alongside the local time so the admin can confirm they match after syncing.

2. `NewOrderScreen`: fetch menu from server, render scrollable list with +/−
   buttons. "OK" → navigate to ShowOrderScreen.

3. `ShowOrderScreen` (new, unsaved): show text receipt preview and total.
   "Salva" → `POST /orders/` → on success, show order id, enable print
   buttons. "Cibo" → `POST /orders/<id>/print/`. "Bar" →
   `POST /orders/<id>/print_drinks/`. "Ricevuta" → print to BLE printer
   (disabled with a clear message if Web Bluetooth unavailable). In sagra
   mode, display a **Fila A / Fila B** indicator (Fila A = drinks + Zeneize
   only, no kitchen print; Fila B = contains food, goes to kitchen).

4. `OrderListScreen`: `GET /orders/` → render list; tap to reload
   `GET /orders/<id>/` and show ShowOrderScreen.

5. **Stats link**: a button/link in the main screen or settings that opens
   `/stats/` in a new tab. Needed from day one so the cashier can check
   totals during the event.

This covers the complete sagra use-case end-to-end.

### Phase 2 — Ristorante mode (tables)

6. `TablesScreen`: `GET /tables/` → render grid. Tap → NewOrderScreen with
   `table` and `waiter` pre-filled.

7. `EditTablesScreen`: same grid, editable waiter names, `PUT /tables/`.

8. In ShowOrderScreen: "Indietro" smart behavior (if just saved and came from
   new-order, go to tables rather than back to new-order).

### Phase 3 — Polish

9. Configurable columns (1–3) for the menu grid.

10. ~~Timestamp sync~~ — moved to Phase 1 (operational requirement).

11. ~~Stats link~~ — moved to Phase 1 (operational requirement).

12. Offline detection: show a banner when `fetch` fails; disable submit
    button until server is reachable.

13. ~~Fila A/B indicator~~ — moved to Phase 1 (operational requirement).

---

## File Structure

```
server/
  static/
    client/
      index.html      ← single-page app shell
      app.js          ← all client logic (~500-800 lines)
      style.css       ← minimal overrides on top of Bootstrap
```

Add one Flask route to serve it:

```python
@ristomele.route('/client/')
def client_app():
    return flask.send_from_directory('static/client', 'index.html')
```

---

## Key Implementation Notes

### Async fetch pattern

The JS app is served from the Flask server, so all API calls use relative
URLs — no host/port configuration needed:

```js
async function apiPost(path, body) {
  const resp = await fetch(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(5000),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}
```

### Error handling

All server calls and BLE operations must catch errors and surface them as
visible, user-friendly messages — never silent failures or raw JS exceptions
in the console only.

- A single `showError(message)` helper renders a dismissible alert (e.g.
  Bootstrap `alert-danger`) at the top of the current screen.
- Server errors: distinguish between network/timeout ("Server non
  raggiungibile") and HTTP error responses (show the status code and body).
- BLE errors: distinguish between "no printer configured" (direct to
  Settings), "connection failed" (suggest retrying), and "Web Bluetooth not
  supported" (permanent, non-dismissible notice on the Ricevuta button).
- Buttons that trigger async operations are disabled while the operation is
  in flight to prevent double-submission.

### Dev mode (console printing)

A `dev_mode` flag in `localStorage` (toggled in `SettingsScreen`) replaces
BLE printing with a `console.log` of the receipt text. This mirrors the
Kivy client's `<Console>` printer option and allows the full order flow to
be tested on a laptop without a physical printer or Bluetooth hardware.

When `dev_mode` is on:
- "Ricevuta" logs the ESC/POS-free receipt text to the browser console
  instead of connecting to a BLE printer.
- A visible indicator (e.g. a small "DEV" badge in the header) reminds the
  user that real printing is disabled.
- Server-side printing ("Cibo", "Bar") is unaffected — those go to the
  server regardless of dev mode.

### Receipt rendering

The server already produces a formatted text receipt (same logic as
`Order.as_textual_receipt()` in the Kivy client). Render it in a `<pre>`
element with a monospaced font (e.g. Roboto Mono, vendored locally). No
HTML table or custom layout — the text format is the decided approach.

### State management

Keep it simple: pass order data through URL params or `sessionStorage`. No
need for a global state store.

- `sessionStorage.setItem('current_order', JSON.stringify(order))` before
  navigating to ShowOrderScreen.
- On startup, fetch `/menu/` and `GET /tables/` in parallel; store both in
  `sessionStorage`. The menu and tables are reused for the whole session
  without re-fetching. Tables can be manually refreshed from the
  TablesScreen if needed (e.g. after EditTablesScreen saves).

### Menu item count state

Each menu item needs a mutable `count` field. Keep the menu as a JS array
in memory during the NewOrderScreen session. Reset to zero when entering a
new order.

### Local Bluetooth printing (customer receipt)

The **Web Bluetooth API** allows a browser page to connect to a BLE printer
and send ESC/POS bytes directly — no native wrapper needed. A working
proof-of-concept exists in `printer-web/web.html` (service/characteristic
discovery + ESC/POS init + text + cut).

**Constraints**:
- Web Bluetooth is only supported in **Chromium-based browsers** (Chrome/Edge
  on Android and desktop). Not available in Firefox or Safari — iOS devices
  cannot print locally. This matches the existing Kivy app behaviour
  (Bluetooth receipt was Android-only there too).
- Web Bluetooth requires a **secure context** (HTTPS or localhost). The Flask
  server must be served over HTTPS. A self-signed certificate is sufficient:
  Chrome will show a one-time "Your connection is not private" warning; after
  clicking "Advanced → Proceed", the page is treated as a secure context and
  Web Bluetooth works normally. **TODO**: verify this on Chrome for Android
  using `printer-web/web.html` before committing to the approach.

Implementation notes:
- On `ShowOrderScreen`, the "Ricevuta" button triggers BLE connect +
  print, using the same ESC/POS sequences as the existing Kivy client.
- Printer selection lives in `SettingsScreen`: a "Seleziona stampante"
  button triggers `navigator.bluetooth.requestDevice()`, and the chosen
  device is saved to `localStorage`. Printing from `ShowOrderScreen`
  reconnects to the saved device silently, without showing the OS
  selection dialog again.
- Chunk large writes (≤512 bytes per `writeValue`) to avoid BLE MTU
  overflows.
- Show a clear error if `navigator.bluetooth` is absent (Firefox/Safari/
  insecure context) rather than silently hiding the button.

---

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Android/iOS route traffic over cellular (no internet WiFi) | Required fix: configure Pi to answer connectivity probes. See `offline-usage.md`. Must be done before going live. |
| CDN assets unavailable (no internet) | All JS/CSS assets must be vendored into `server/static/client/`. No CDN links anywhere. |
| Web Bluetooth requires HTTPS | Serve Flask over HTTPS with a self-signed cert; users click "proceed anyway" once. See `offline-usage.md`. Verify on Chrome/Android using the PoC before committing. |
| Web Bluetooth not available on Firefox/Safari | "Ricevuta" button shows a clear error message; kitchen/bar printing via server is unaffected. |

---

## Rough Effort Estimate

| Phase | Description | Estimated effort |
|-------|-------------|-----------------|
| 1 | Sagra workflow (settings + timestamp sync, new order, show/save + Fila A/B, list, stats link) | ~1.5 days |
| 2 | Ristorante mode (tables) | ~0.5 day |
| 3 | Polish (columns, offline detection banner) | ~0.5 day |
| — | `GET /menu/` server endpoint (menu + mode) | ~1 hour |
| **Total** | | **~2–3 days** |

---

## Optional: Progressive Web App

Once the basic client works, adding a Web App Manifest and a minimal Service
Worker would allow "Add to Home Screen" on Android, giving an app-like
experience without needing an APK. The service worker can cache the app shell
for offline startup, while all API calls require the server.
