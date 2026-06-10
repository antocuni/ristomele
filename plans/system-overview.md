# RistoMele — System Overview

## Purpose

RistoMele manages food and drink orders for small town food festivals ("sagra")
and sit-down restaurant events. It supports two main operational modes:

- **ristorante**: waiters carry phones to tables, assign themselves to tables,
  take orders table-by-table. Two receipt copies (one for the kitchen, one for
  the customer).
- **sagra** (food festival): customers queue at a counter ("cassa"), a cashier
  takes the order. "Fila A" orders (drinks + Zeneize flatbread only) are not
  sent to the kitchen printer. "Fila B" orders (contain real food) go to the
  kitchen printer, but without the drinks section.
- **croce**: a variant similar to sagra, no table assignment, used for a
  different venue ("Croce Verde").

The `is_sagra` / `is_croce` flags are set per-client in `ristomele.ini` and
also mirrored in `server/config.py:MODE`.

---

## Components

```
┌─────────────────────────────────────────────────────────────────┐
│  Raspberry Pi (server)                                          │
│                                                                 │
│  ┌─────────────────┐    spool files    ┌──────────────────────┐ │
│  │  Flask/uwsgi    │ ────────────────► │  Spooler process     │ │
│  │  (port 5000)    │  /tmp/spooldir/   │  (polls every 1s)    │ │
│  │                 │  food/*.txt       │                      │ │
│  │  SQLite DB      │  drinks/*.txt     │  Writes to           │ │
│  │  db.sqlite      │                  │  /dev/usb/lp*        │ │
│  └────────┬────────┘                  └──────────────────────┘ │
│           │ HTTP (port 5000)               │                   │
└───────────┼────────────────────────────────┼───────────────────┘
            │                                │
            │ WiFi / LAN                     │ USB
            │                                │
┌───────────┴──────────┐          ┌──────────┴────────────┐
│  Kivy Client         │          │  Thermal printers      │
│  (Android / Linux)   │          │  food: USB port 1-1.1  │
│                      │          │  drinks: USB port 1-1.3│
│  Bluetooth printing  │          └───────────────────────┘
│  (client receipt)    │
└──────────────────────┘
```

### Server (`server/`)

- **Framework**: Flask + Flask-SQLAlchemy, deployed via uwsgi
- **Database**: SQLite (`db.sqlite`), one file per year, backed up manually
- **Entry point**: `server/app.py:create_app()` / `create_logged_app()`
- **Blueprints**:
  - `ristomele` (`server/ristomele.py`) — all business logic routes
  - `srczip` (`server/srczip.py`) — serves the mobile source code for
    auto-update
- **Printing**: server writes ESC/POS text files to `/tmp/spooldir/food/` and
  `/tmp/spooldir/drinks/`; the separate spooler process picks them up.

### Spooler (`server/spooler.py`)

A standalone Python process (managed by a systemd service). Polls
`/tmp/spooldir/food/` and `/tmp/spooldir/drinks/` every second. Detects
thermal printers by USB physical port topology (hardcoded in the code):

- food printers: ports `1-1.1`, `1-1.2`
- drinks printers: ports `1-1.3`, `1-1.4`

Writes receipt content directly to `/dev/usb/lp*`.

### Client (`mobile/`)

- **Framework**: Kivy (Python)
- **Platforms**: Android (APK) and Linux/desktop
- **Auto-update**: on startup, client fetches `/mobile/md5`; if source has
  changed (or it's a fresh install), downloads `/mobile/download` (a zip of
  `mobile/src/`) and extracts it, then dynamically imports the app. Falls back
  to a minimal "bootstrap" settings app if the server is unreachable.
- **Local printing**: client can print a customer receipt to a Bluetooth
  thermal printer (Android) or the first available `/dev/usb/lp*` (Linux).

---

## REST API

Base URL: `http://<server_ip>:5000`

All request/response bodies are JSON unless otherwise noted.

### Orders

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/orders/` | Create a new order; triggers printing on the server |
| `GET`  | `/orders/` | List all orders (light: `menu` field is `null`) |
| `GET`  | `/orders/<id>/` | Get a single order with full `menu` |
| `POST` | `/orders/<id>/print/` | Reprint the food receipt for an existing order |
| `POST` | `/orders/<id>/print_drinks/` | Reprint the drinks receipt |

**Order object (POST /orders/ request body)**:
```json
{
  "cashier": "gian",
  "table": "11",
  "waiter": "anto",
  "customer": "pippo",
  "notes": "allergia noci",
  "menu": [
    {"kind": "separator", "name": "Primi", "count": 0, "price": 0, "is_drink": false},
    {"kind": "item",      "name": "Trenette al pesto", "count": 2, "price": 6.5, "is_drink": false},
    {"kind": "item",      "name": "Birra PILS",         "count": 1, "price": 5.0, "is_drink": true}
  ]
}
```

**Response** (POST /orders/):
```json
{
  "result": "OK",
  "order": {
    "id": 42,
    "date": "2025-08-14 20:30:00",
    "cashier": "gian",
    "table": "11",
    "waiter": "anto",
    "customer": "pippo",
    "notes": "allergia noci",
    "menu": [ ... ]
  }
}
```

### Tables

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/tables/` | List all tables with their assigned waiter |
| `PUT`  | `/tables/<name>/` | Update a single table's waiter |
| `PUT`  | `/tables/` | Update multiple tables at once |

**Table object**:
```json
{"name": "11", "waiter": "anto"}
```

### Utility

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/timestamp/` | Get current server UNIX timestamp |
| `POST` | `/timestamp/` | Set server time (`{"timestamp": 1723657800.0}`) |
| `GET`  | `/stats/` | HTML stats page (orders/revenue by day and cashier) |
| `GET`  | `/apk/` | Download the Android APK |
| `GET`  | `/mobile/md5` | MD5 hash of the current mobile source zip |
| `GET`  | `/mobile/download` | Download `src.zip` (mobile Python source) |

---

## Data Models

### MenuItem
```
kind:     "item" | "separator"
name:     string
count:    int   (0 = not ordered)
price:    float (euros)
is_drink: bool
```

Separators are visual section headers in the menu (e.g. "Primi", "Bibite").
Their `count`, `price`, `is_drink` are always 0/False. They are included in
the `menu` array stored in the order so the receipt can recreate the layout.

### Order (DB)
```
id:       int (autoincrement)
date:     datetime (UTC, server-assigned on POST)
cashier:  string  (person at the cash register)
table:    string  (table name, "N/A" in sagra mode)
waiter:   string  (waiter serving the table, "N/A" in sagra mode)
customer: string  (free text, name of the customer/group)
notes:    string  (free text, e.g. allergies)
menu:     JSON string  (array of MenuItem dicts)
```

**`date_dwim`**: orders placed between midnight and 3am are attributed to the
previous calendar day (festival days run past midnight).

### Table (DB)
```
name:   string (PK, e.g. "1" through "15")
waiter: string
```

---

## Menu Definition

The menu is hardcoded in `mobile/src/ristomele/menu.py`. The active menu is
selected by editing the `get_menu()` function. Multiple named menus exist for
different events (e.g. `menu_14_agosto`, `menu_sagra`, `menu_croce`).

When an order is created, the full menu (with all items, even those with
`count=0`) is sent to the server and stored as JSON. This means the server
preserves the exact menu snapshot for each order.

---

## Print Logic

### Server-side (thermal receipt)

On `POST /orders/`, the server calls:

1. `do_print_order(order)` — writes to `spooldir/food/order_XXXXXX.txt`
   - In **sagra** mode: skipped entirely if the order is "Fila A" (only drinks
     + Zeneize items). Drinks are excluded from the food receipt in sagra mode.
   - In **ristorante** mode: always printed; includes drinks.

2. `do_print_drinks(order)` — writes to `spooldir/drinks/order_XXXXXX.txt`
   - Only written if the order contains at least one drink (`is_drink=True`).

Receipt text uses ESC/POS escape sequences (`server/escpos.py`) for bold/large
fonts and paper feed. Unicode is encoded as CP858.

### Client-side (Bluetooth / local USB receipt)

The client can also print a customer receipt directly to a local Bluetooth
printer (Android) or the first available `/dev/usb/lp*` (Linux). This receipt
includes the full itemized list with subtotals, grand total, and "RICEVUTA NON
FISCALE" disclaimer. In ristorante mode it prints two copies (customer +
waiter).

---

## Client Screens

```
MainScreen
├── (sagra/croce) NewOrderScreen ──► ShowOrderScreen
├── (ristorante)  TablesScreen ──► NewOrderScreen ──► ShowOrderScreen
├── EditTablesScreen
├── OrderListScreen ──► ShowOrderScreen
└── AdvancedOptionsScreen
    ├── set server timestamp
    ├── open stats (browser)
    └── Bluetooth info (Android only)
```

### NewOrderScreen

Scrollable grid of menu items. Each `MenuItem` row has:
- `[-]` button: decrement count (min 0)
- count label
- `[+]` button: increment count
- item name label

Separators span the full width and are displayed as bold section headers.
The number of columns is configurable (default 1, up to 3).

Text inputs at the top: customer name, notes.

### ShowOrderScreen

Shows a monospaced text receipt preview (same format as the printed receipt).
Displays total; has a cash calculator (enter amount received → shows change).

Buttons:
- **Salva** (before saving) / **Cibo** (after saving): submit to server / reprint food
- **Bar**: print drinks receipt
- **Ricevuta**: print local Bluetooth/USB customer receipt
- **Indietro**: go back (if already saved, goes back to tables/main screen)

---

## Configuration

### Server: `server/config.py`

```python
MODE = 'ristorante'  # or 'sagra'
```

### Client: `mobile/ristomele.ini`

```ini
[server]
host = 192.168.1.6
port = 5000
timeout = 3

[ristomele]
cashier = gian
printer = <device name>
is_sagra = 0
is_croce = 0
columns = 1
```

`cashier` is the name of the person using this device (shown on receipts).
`printer` is the Bluetooth device name (Android) or `<Auto>`/`<Console>`
(Linux).

---

## Deployment

- Server runs on a Raspberry Pi on the local WiFi network.
- `service ristomele` — uwsgi Flask server, port 5000
- `service ristomele-spooler` — spooler process
- Clients connect over WiFi; no internet required.
- The APK is downloaded from `http://<server>:5000/apk/` at setup time.
- Source auto-update: every client startup fetches the latest source from the
  server and hot-reloads it, so deploying a client update only requires
  updating the server's `mobile/src/` directory.
