'use strict';

// ─── Local settings (localStorage) ──────────────────────────────────────────

function gs(key, def) { var v = localStorage.getItem(key); return v !== null ? v : (def !== undefined ? def : ''); }
function ss(key, val) { localStorage.setItem(key, String(val)); }

// ─── API ─────────────────────────────────────────────────────────────────────

async function apiFetch(path, opts) {
    opts = opts || {};
    var controller = new AbortController();
    var tid = setTimeout(function() { controller.abort(); }, 5000);
    try {
        var resp = await fetch(path, Object.assign({}, opts, { signal: controller.signal }));
        clearTimeout(tid);
        hideOfflineBanner();
        if (!resp.ok) {
            var body = '';
            try { body = await resp.text(); } catch (_) {}
            throw new Error('HTTP ' + resp.status + ': ' + body);
        }
        return resp.json();
    } catch (e) {
        clearTimeout(tid);
        if (e.name === 'AbortError' || e instanceof TypeError) {
            showOfflineBanner();
            throw new Error('Server non raggiungibile');
        }
        throw e;
    }
}

var api = {
    get: function(path) { return apiFetch(path); },
    post: function(path, body) {
        return apiFetch(path, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) });
    },
    put: function(path, body) {
        return apiFetch(path, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) });
    },
};

// ─── Menu config (session cache) ─────────────────────────────────────────────

var _menuConfig = null;

async function getMenuConfig() {
    if (_menuConfig) return _menuConfig;
    _menuConfig = await api.get('/menu/');
    return _menuConfig;
}

// ─── Receipt logic ───────────────────────────────────────────────────────────

var RECEIPT_WIDTH = 32;

function isFilaA(menu) {
    for (var i = 0; i < menu.length; i++) {
        var item = menu[i];
        if (item.count > 0 && !item.is_drink && item.name.indexOf('Zeneize') === -1) return false;
    }
    return true;
}

function computeTotal(menu) {
    var total = 0;
    for (var i = 0; i < menu.length; i++) {
        if (menu[i].kind === 'item') total += menu[i].count * menu[i].price;
    }
    return total;
}

function formatDateShort(dateStr) {
    // "2025-08-14 20:30:00" → "14/08 20:30"
    var d = new Date(dateStr.replace(' ', 'T'));
    var dd = String(d.getDate()).padStart(2, '0');
    var mm = String(d.getMonth() + 1).padStart(2, '0');
    var hh = String(d.getHours()).padStart(2, '0');
    var mn = String(d.getMinutes()).padStart(2, '0');
    return dd + '/' + mm + ' ' + hh + ':' + mn;
}

function renderReceiptText(order, cfg, title) {
    var W = RECEIPT_WIDTH;
    var lines = [];
    function w(s) { lines.push(s); }

    w(title || '');

    var num = order.id != null ? String(order.id) : '';
    var date = order.date ? '[' + formatDateShort(order.date) + ']' : '';
    var orderLine = ('Numero ordine: ' + num + ' ' + date).trimEnd ? ('Numero ordine: ' + num + ' ' + date).trimEnd() : ('Numero ordine: ' + num + ' ' + date).replace(/\s+$/, '');

    if (cfg.is_sagra) {
        w(isFilaA(order.menu) ? 'Fila A' : 'Fila B');
        w(orderLine);
        w('Cassiere: ' + (order.cashier || ''));
        w('Cliente: ' + (order.customer || ''));
    } else if (cfg.is_croce) {
        w(orderLine);
        w('Cassiere: ' + (order.cashier || ''));
        w('Cliente: ' + (order.customer || ''));
        w('Tavolo:');
    } else {
        w(orderLine);
        w('Tavolo: ' + (order.table || 'N/A') + ' [' + (order.waiter || '') + ']');
        w('Cassiere: ' + (order.cashier || ''));
        w('Cliente: ' + (order.customer || ''));
    }

    w('');

    for (var i = 0; i < order.menu.length; i++) {
        var item = order.menu[i];
        if (item.kind !== 'item' || item.count === 0) continue;
        var subtot = item.count * item.price;
        var countStr = ('x' + item.count).padEnd ? ('x' + item.count).padEnd(3) : ('x' + item.count + '   ').substring(0, 3);
        var amtStr = subtot.toFixed(2).padStart ? subtot.toFixed(2).padStart(5) : ('     ' + subtot.toFixed(2)).slice(-5);
        var priceStr = countStr + ' ' + amtStr + ' €'; // 11 chars
        var descr = (item.name + ' ').substring(0, W);
        if (descr.length + priceStr.length > W) {
            w(descr);
            w(priceStr.padStart ? priceStr.padStart(W) : ('                                ' + priceStr).slice(-W));
        } else {
            var pad = W - descr.length;
            w(descr + (priceStr.padStart ? priceStr.padStart(pad) : ('                                ' + priceStr).slice(-pad)));
        }
    }

    w('');
    var totLine = 'TOTALE: ' + computeTotal(order.menu).toFixed(2) + ' €';
    w(totLine.padStart ? totLine.padStart(W) : ('                                ' + totLine).slice(-W));
    w('');
    w('RICEVUTA NON FISCALE');

    return lines.join('\n');
}

// ─── BLE printing ────────────────────────────────────────────────────────────

// Cached BLE state — survives within the same tab session.
var _bleDevice = null;   // BluetoothDevice
var _bleServer = null;   // BluetoothRemoteGATTServer (may be disconnected)
var _bleChr    = null;   // cached write characteristic

// Cached USB state
var _usbDevice   = null; // USBDevice
var _usbEpNum    = null; // bulk-OUT endpoint number
var _usbIfaceNum = null; // claimed interface number

var PRINTER_SERVICES = [
    'e7810a71-73ae-499d-8c15-faa9aef0c3f2',
    '000018f0-0000-1000-8000-00805f9b34fb',
    '49535343-fe7d-4ae5-8fa9-9fafd205e455',
    '6e400001-b5a3-f393-e0a9-e50e24dcca9e',
];
var PRINTER_CHARS = [
    'bef8d6c9-9c21-4c9e-b632-bd58c1009f9f',
    '000018f1-0000-1000-8000-00805f9b34fb',
    '49535343-1e4d-4bd9-ba61-23c647249616',
    '6e400002-b5a3-f393-e0a9-e50e24dcca9e',
];

async function findPrintChar(server) {
    for (var si = 0; si < PRINTER_SERVICES.length; si++) {
        try {
            var svc = await server.getPrimaryService(PRINTER_SERVICES[si]);
            for (var ci = 0; ci < PRINTER_CHARS.length; ci++) {
                try {
                    var chr = await svc.getCharacteristic(PRINTER_CHARS[ci]);
                    if (chr.properties.write || chr.properties.writeWithoutResponse) return chr;
                } catch (_) {}
            }
        } catch (_) {}
    }
    var services = await server.getPrimaryServices().catch(function() { return []; });
    for (var i = 0; i < services.length; i++) {
        var chars = await services[i].getCharacteristics().catch(function() { return []; });
        for (var j = 0; j < chars.length; j++) {
            if (chars[j].properties.write || chars[j].properties.writeWithoutResponse) return chars[j];
        }
    }
    return null;
}

async function bleWriteChunked(chr, data) {
    var CHUNK = 100;
    for (var i = 0; i < data.length; i += CHUNK) {
        await chr.writeValue(data.slice(i, i + CHUNK));
        await new Promise(function(r) { setTimeout(r, 20); });
    }
}

async function bleGetDevice() {
    var deviceId   = gs('ble_device_id');
    var deviceName = gs('ble_device_name');

    // 1. If we already have a cached device that matches by id, reuse it.
    if (_bleDevice && _bleDevice.id === deviceId) return _bleDevice;

    // 2. Try getDevices() — returns previously-granted devices without picker.
    if (navigator.bluetooth.getDevices) {
        var granted = await navigator.bluetooth.getDevices();
        var found = null;
        for (var i = 0; i < granted.length; i++) {
            if (deviceId && granted[i].id === deviceId) { found = granted[i]; break; }
            if (!deviceId && granted[i].name === deviceName) { found = granted[i]; break; }
        }
        if (found) { _bleDevice = found; return _bleDevice; }
    }

    // 3. Fall back to the picker (first use only).
    var filterOnly = gs('ble_filter_printers', '1') === '1';
    var opts = filterOnly
        ? { filters: PRINTER_SERVICES.map(function(s) { return { services: [s] }; }), optionalServices: PRINTER_SERVICES }
        : { acceptAllDevices: true, optionalServices: PRINTER_SERVICES };
    _bleDevice = await navigator.bluetooth.requestDevice(opts);
    return _bleDevice;
}

function bleConnectWithTimeout(gatt, ms) {
    return Promise.race([
        gatt.connect(),
        new Promise(function(_, reject) {
            setTimeout(function() { reject(new Error('Stampante BLE non raggiungibile (timeout).')); }, ms);
        }),
    ]);
}

async function bleGetConnection() {
    var deviceId = gs('ble_device_id');
    // If the user picked a different printer in Settings, drop the old connection.
    if (_bleDevice && _bleDevice.id !== deviceId) {
        if (_bleServer && _bleServer.connected) try { _bleServer.disconnect(); } catch (_) {}
        _bleDevice = null; _bleServer = null; _bleChr = null;
    }
    // Reuse existing connected server+characteristic if possible.
    if (_bleServer && _bleServer.connected && _bleChr) return _bleChr;

    _bleChr = null;
    if (_bleServer && !_bleServer.connected) {
        // Reconnect silently — no picker.
        try { await bleConnectWithTimeout(_bleServer, 8000); } catch (_) { _bleServer = null; }
    }
    if (!_bleServer || !_bleServer.connected) {
        var device = await bleGetDevice();
        _bleServer = await bleConnectWithTimeout(device.gatt, 8000);
    }
    _bleChr = await findPrintChar(_bleServer);
    if (!_bleChr) { _bleServer.disconnect(); _bleServer = null; throw new Error('Caratteristica di stampa non trovata sulla stampante.'); }
    return _bleChr;
}

function encodeWPC1252(text) {
    // WPC1252 is identical to Latin-1 for 0x00–0x7F and 0xA0–0xFF.
    // The only receipt character outside that range is €, which sits at 0x80.
    var bytes = new Uint8Array(text.length);
    for (var i = 0; i < text.length; i++) {
        var c = text.charCodeAt(i);
        if (c === 0x20AC) { bytes[i] = 0x80; }  // €
        else if (c <= 0xFF) { bytes[i] = c; }
        else { bytes[i] = 0x3F; }               // ? for anything else
    }
    return bytes;
}

async function blePrintText(text) {
    if (!navigator.bluetooth) throw new Error('Web Bluetooth non supportato. Usa Chrome/Edge su Android o desktop.');
    var deviceName = gs('ble_device_name');
    if (!deviceName) throw new Error('Nessuna stampante configurata. Vai in Impostazioni e seleziona una stampante.');

    var chr = await bleGetConnection();
    await chr.writeValue(new Uint8Array([0x1B, 0x40]));        // ESC @      — init
    await chr.writeValue(new Uint8Array([0x1B, 0x74, 0x10])); // ESC t 16  — WPC1252
    await bleWriteChunked(chr, encodeWPC1252(text));
    await chr.writeValue(new Uint8Array([0x1B, 0x64, 0x03])); // ESC d 3   — feed 3 lines
    // Leave connection open for next print.
}

async function bleSelectPrinter() {
    if (!navigator.bluetooth) throw new Error('Web Bluetooth non supportato in questo browser.');
    var filterOnly = gs('ble_filter_printers', '1') === '1';
    var opts = filterOnly
        ? { filters: PRINTER_SERVICES.map(function(s) { return { services: [s] }; }), optionalServices: PRINTER_SERVICES }
        : { acceptAllDevices: true, optionalServices: PRINTER_SERVICES };
    var device = await navigator.bluetooth.requestDevice(opts);
    ss('ble_device_name', device.name);
    ss('ble_device_id',   device.id);
    // Cache the device and eagerly connect so subsequent calls skip the picker.
    _bleDevice = device;
    _bleServer = null; _bleChr = null;
    try {
        _bleServer = await device.gatt.connect();
        _bleChr = await findPrintChar(_bleServer);
    } catch (_) {
        // Connection attempt failed — will retry on first print, no picker needed.
        _bleServer = null; _bleChr = null;
    }
    return device;
}

// ─── USB printing ────────────────────────────────────────────────────────────

function usbFindBulkOut(device) {
    for (var ci = 0; ci < device.configurations.length; ci++) {
        var cfg = device.configurations[ci];
        for (var ii = 0; ii < cfg.interfaces.length; ii++) {
            var iface = cfg.interfaces[ii];
            for (var ai = 0; ai < iface.alternates.length; ai++) {
                var alt = iface.alternates[ai];
                for (var ei = 0; ei < alt.endpoints.length; ei++) {
                    var ep = alt.endpoints[ei];
                    if (ep.type === 'bulk' && ep.direction === 'out') {
                        return { ifaceNum: iface.interfaceNumber, altSetting: alt.alternateSetting, epNum: ep.endpointNumber };
                    }
                }
            }
        }
    }
    return null;
}

async function usbSelectPrinter() {
    if (!navigator.usb) throw new Error('WebUSB non supportato in questo browser.');
    var device = await navigator.usb.requestDevice({ filters: [] });
    var name = ((device.productName || device.manufacturerName || '').trim()) || ('USB #' + device.productId.toString(16));
    ss('usb_device_name', name);
    ss('usb_vendor_id',   String(device.vendorId));
    ss('usb_product_id',  String(device.productId));
    _usbDevice = device; _usbEpNum = null; _usbIfaceNum = null;
    return device;
}

async function usbGetConnection() {
    var vendorId  = parseInt(gs('usb_vendor_id'),  10);
    var productId = parseInt(gs('usb_product_id'), 10);
    if (!vendorId || !productId) throw new Error('Nessuna stampante USB configurata. Vai in Impostazioni e seleziona una stampante.');

    if (_usbDevice && (_usbDevice.vendorId !== vendorId || _usbDevice.productId !== productId)) {
        try { if (_usbDevice.opened) await _usbDevice.close(); } catch (_) {}
        _usbDevice = null; _usbEpNum = null; _usbIfaceNum = null;
    }

    if (!_usbDevice || !_usbDevice.opened) {
        if (!_usbDevice && navigator.usb.getDevices) {
            var granted = await navigator.usb.getDevices();
            for (var i = 0; i < granted.length; i++) {
                if (granted[i].vendorId === vendorId && granted[i].productId === productId) { _usbDevice = granted[i]; break; }
            }
        }
        if (!_usbDevice) throw new Error('Stampante USB non trovata. Collegala e riprova.');
        _usbEpNum = null; _usbIfaceNum = null;
        await _usbDevice.open();
        if (_usbDevice.configuration === null) await _usbDevice.selectConfiguration(1);
    }

    if (_usbEpNum === null) {
        var found = usbFindBulkOut(_usbDevice);
        if (!found) { await _usbDevice.close(); _usbDevice = null; throw new Error('Endpoint di stampa USB non trovato sulla stampante.'); }
        try {
            await _usbDevice.claimInterface(found.ifaceNum);
        } catch (e) {
            _usbDevice = null; _usbEpNum = null;
            var ce = new Error('usb_claim_failed');
            ce.isUsbClaimError = true;
            throw ce;
        }
        await _usbDevice.selectAlternateInterface(found.ifaceNum, found.altSetting);
        _usbIfaceNum = found.ifaceNum;
        _usbEpNum    = found.epNum;
    }
    return _usbEpNum;
}

async function usbPrintText(text) {
    if (!navigator.usb) throw new Error('WebUSB non supportato. Usa Chrome/Edge su Android o desktop.');
    if (!gs('usb_device_name')) throw new Error('Nessuna stampante USB configurata. Vai in Impostazioni e seleziona una stampante.');
    var epNum = await usbGetConnection();
    var CHUNK = 512;
    async function send(bytes) { await _usbDevice.transferOut(epNum, bytes); }
    await send(new Uint8Array([0x1B, 0x40]));        // ESC @      — init
    await send(new Uint8Array([0x1B, 0x74, 0x10])); // ESC t 16  — WPC1252
    var data = encodeWPC1252(text);
    for (var i = 0; i < data.length; i += CHUNK) await send(data.slice(i, i + CHUNK));
    await send(new Uint8Array([0x1B, 0x64, 0x03])); // ESC d 3   — feed 3 lines
}

// ─── Unified print ───────────────────────────────────────────────────────────

async function printText(text) {
    if (gs('print_via', 'ble') === 'dev') { console.log('=== RICEVUTA ===\n' + text); return; }
    if (gs('print_via', 'ble') === 'usb') {
        try {
            await usbPrintText(text);
        } catch (e) {
            if (e.isUsbClaimError) { showUsbClaimModal(); } else { throw e; }
        }
        return;
    } else {
        await blePrintText(text);
    }
}

// ─── UI helpers ──────────────────────────────────────────────────────────────

function esc(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

var _offlineTimer = null;

function showOfflineBanner() {
    $id('offline-bar').style.display = '';
    document.body.classList.add('offline-mode');
    if (_offlineTimer) return;
    _offlineTimer = setInterval(async function() {
        try {
            await fetch('/timestamp/', { signal: AbortSignal.timeout(3000) });
            hideOfflineBanner();
        } catch (_) {}
    }, 5000);
}

function hideOfflineBanner() {
    $id('offline-bar').style.display = 'none';
    document.body.classList.remove('offline-mode');
    if (_offlineTimer) { clearInterval(_offlineTimer); _offlineTimer = null; }
}

function showUsbClaimModal() {
    showModal(
        '<h4>Stampante USB non accessibile</h4>' +
        '<p>Il sistema operativo ha già occupato l\'interfaccia USB della stampante e il browser non riesce ad accedervi.</p>' +
        '<p>Su Linux, esegui questo comando e riprova:</p>' +
        '<code>sudo modprobe -r usblp</code>'
    );
}

function showModal(html) {
    $id('modal-body').innerHTML = html;
    $id('modal-overlay').style.display = 'flex';
}

function hideModal() {
    $id('modal-overlay').style.display = 'none';
}

function showError(msg) {
    showModal('<p style="color:#a94442">' + esc(msg) + '</p>');
}

function hideError() {
    // Errors are now modals — dismissed explicitly by the user, not on navigation.
}

function setContent(html) { document.getElementById('app').innerHTML = html; }

function setTitle(t) { document.getElementById('screen-title').textContent = t; }

function setBack(hashOrFn) {
    var btn = document.getElementById('back-btn');
    if (hashOrFn) {
        btn.style.display = '';
        btn.onclick = typeof hashOrFn === 'function' ? hashOrFn : function() { navigate(hashOrFn); };
    } else {
        btn.style.display = 'none';
        btn.onclick = null;
    }
}

function updateDevBadge() {
    document.getElementById('dev-badge').style.display = gs('print_via', 'ble') === 'dev' ? '' : 'none';
}

function navigate(hash) { location.hash = hash; }

function disableBtn(id, disabled) {
    var el = document.getElementById(id);
    if (el) el.disabled = disabled;
}

function $id(id) { return document.getElementById(id); }

// ─── Screens ─────────────────────────────────────────────────────────────────

async function screenMain() {
    hideError();
    var cfg;
    try { cfg = await getMenuConfig(); }
    catch (e) { showError('Impossibile connettersi al server: ' + e.message); cfg = { is_sagra: false, is_croce: false }; }

    setTitle('Menu Principale');
    setBack(null);

    var isRist = !cfg.is_sagra && !cfg.is_croce;
    var newOrderBtn = (cfg.is_sagra || cfg.is_croce)
        ? '<a href="#/order/new" class="list-group-item main-item">Nuovo ordine <span class="main-chevron">›</span></a>'
        : '<a href="#/tables"    class="list-group-item main-item">Mappa tavoli <span class="main-chevron">›</span></a>';

    setContent(
        '<div class="container-fluid" style="padding-top:12px">' +
            '<div class="list-group">' +
                newOrderBtn +
                '<a href="#/orders"      class="list-group-item main-item">Lista ordini <span class="main-chevron">›</span></a>' +
                (isRist ? '<a href="#/tables/edit" class="list-group-item main-item">Configura tavoli <span class="main-chevron">›</span></a>' : '') +
                '<a href="#/settings"    class="list-group-item main-item">Impostazioni <span class="main-chevron">›</span></a>' +
                '<a href="/stats/" target="_blank" class="list-group-item main-item">Statistiche <span class="main-chevron">›</span></a>' +
            '</div>' +
        '</div>'
    );
}

async function screenSettings() {
    hideError();
    setTitle('Impostazioni');
    setBack('#/');

    var cashier        = gs('cashier');
    var bleName        = gs('ble_device_name');
    var bleId          = gs('ble_device_id');
    var bleLabel       = bleName ? bleName + (bleId ? ' [' + bleId.slice(-8) + ']' : '') : '(nessuna)';
    var bleFilterOnly  = gs('ble_filter_printers', '1') === '1';
    var cols           = gs('columns', '1');
    var printVia       = gs('print_via', 'ble');
    var usbLabel       = gs('usb_device_name') || '(nessuna)';

    var serverTimeHtml = '<em>caricamento...</em>';

    setContent(
        '<div class="settings-form">' +
            '<div class="form-group">' +
                '<label>Nome cassiere</label>' +
                '<input type="text" id="inp-cashier" class="form-control" value="' + esc(cashier) + '">' +
            '</div>' +
            '<div class="form-group">' +
                '<label>Metodo di stampa</label>' +
                '<select id="sel-print-via" class="form-control">' +
                    '<option value="ble"' + (printVia === 'ble' ? ' selected' : '') + '>Bluetooth (BLE)</option>' +
                    '<option value="usb"' + (printVia === 'usb' ? ' selected' : '') + '>USB</option>' +
                    '<option value="dev"' + (printVia === 'dev' ? ' selected' : '') + '>Console (sviluppo)</option>' +
                '</select>' +
            '</div>' +
            '<div id="sec-ble" class="form-group"' + (printVia !== 'ble' ? ' style="display:none"' : '') + '>' +
                '<label>Stampante BLE</label>' +
                '<div class="input-group">' +
                    '<span class="input-group-addon" id="ble-name">' + esc(bleLabel) + '</span>' +
                    '<span class="input-group-btn">' +
                        '<button id="btn-ble" class="btn btn-default" type="button">Seleziona</button>' +
                    '</span>' +
                '</div>' +
                '<button id="btn-test-print" class="btn btn-default btn-sm" style="margin-top:6px">Prova stampa</button>' +
                '<div class="checkbox" style="margin-top:4px"><label>' +
                    '<input type="checkbox" id="chk-ble-filter" ' + (bleFilterOnly ? 'checked' : '') + '> ' +
                    'Mostra solo stampanti' +
                '</label></div>' +
            '</div>' +
            '<div id="sec-usb" class="form-group"' + (printVia !== 'usb' ? ' style="display:none"' : '') + '>' +
                '<label>Stampante USB</label>' +
                '<div class="input-group">' +
                    '<span class="input-group-addon" id="usb-name">' + esc(usbLabel) + '</span>' +
                    '<span class="input-group-btn">' +
                        '<button id="btn-usb" class="btn btn-default" type="button">Seleziona</button>' +
                    '</span>' +
                '</div>' +
                '<button id="btn-test-print-usb" class="btn btn-default btn-sm" style="margin-top:6px">Prova stampa</button>' +
            '</div>' +
            '<div class="form-group">' +
                '<label>Colonne menu</label>' +
                '<select id="sel-columns" class="form-control">' +
                    '<option value="1"' + (cols === '1' ? ' selected' : '') + '>1 colonna</option>' +
                    '<option value="2"' + (cols === '2' ? ' selected' : '') + '>2 colonne</option>' +
                    '<option value="3"' + (cols === '3' ? ' selected' : '') + '>3 colonne</option>' +
                '</select>' +
            '</div>' +
            '<hr>' +
            '<div class="form-group">' +
                '<p>Ora server: <strong id="lbl-server-time">' + serverTimeHtml + '</strong></p>' +
                '<p>Ora locale: <strong>' + new Date().toLocaleString('it-IT') + '</strong></p>' +
                '<button id="btn-sync" class="btn btn-warning">Sincronizza ora</button>' +
            '</div>' +
            '<hr>' +
            '<button id="btn-save" class="btn btn-primary btn-block">Salva</button>' +
        '</div>'
    );

    // Load server time async
    api.get('/timestamp/').then(function(ts) {
        var el = $id('lbl-server-time');
        if (el) el.textContent = new Date(ts.timestamp * 1000).toLocaleString('it-IT');
    }).catch(function() {
        var el = $id('lbl-server-time');
        if (el) el.textContent = 'non disponibile';
    });

    $id('btn-save').onclick = function() {
        ss('cashier',             $id('inp-cashier').value.trim());
        ss('columns',             $id('sel-columns').value);
        ss('ble_filter_printers', $id('chk-ble-filter').checked ? '1' : '0');
        ss('print_via',           $id('sel-print-via').value);
        updateDevBadge();
        navigate('#/');
    };

    $id('btn-ble').onclick = async function() {
        disableBtn('btn-ble', true);
        try {
            var dev = await bleSelectPrinter();
            var label = dev.name + (dev.id ? ' [' + dev.id.slice(-8) + ']' : '');
            $id('ble-name').textContent = label;
        } catch (e) {
            showError(e.message);
        } finally {
            disableBtn('btn-ble', false);
        }
    };

    $id('btn-test-print').onclick = async function() {
        disableBtn('btn-test-print', true);
        try {
            await blePrintText('Prova stampa RistoMele\n');
        } catch (e) {
            showError(e.message);
        } finally {
            disableBtn('btn-test-print', false);
        }
    };

    $id('sel-print-via').onchange = function() {
        var v = this.value;
        $id('sec-ble').style.display = v === 'ble' ? '' : 'none';
        $id('sec-usb').style.display = v === 'usb' ? '' : 'none';
        updateDevBadge();
    };

    $id('btn-usb').onclick = async function() {
        disableBtn('btn-usb', true);
        try {
            var dev = await usbSelectPrinter();
            var label = ((dev.productName || dev.manufacturerName || '').trim()) || ('USB #' + dev.productId.toString(16));
            $id('usb-name').textContent = label;
        } catch (e) {
            showError(e.message);
        } finally {
            disableBtn('btn-usb', false);
        }
    };

    $id('btn-test-print-usb').onclick = async function() {
        disableBtn('btn-test-print-usb', true);
        try {
            await usbPrintText('Prova stampa RistoMele\n');
        } catch (e) {
            if (e.isUsbClaimError) { showUsbClaimModal(); } else { showError(e.message); }
        } finally {
            disableBtn('btn-test-print-usb', false);
        }
    };

    $id('btn-sync').onclick = async function() {
        disableBtn('btn-sync', true);
        try {
            await api.post('/timestamp/', { timestamp: Date.now() / 1000 });
            var ts2 = await api.get('/timestamp/');
            $id('lbl-server-time').textContent = new Date(ts2.timestamp * 1000).toLocaleString('it-IT');
        } catch (e) {
            showError(e.message);
        } finally {
            disableBtn('btn-sync', false);
        }
    };
}

// Items kept in memory while NewOrderScreen is active
var _orderItems = [];

async function screenNewOrder() {
    hideError();
    var cfg = await getMenuConfig();

    var tableFromSession = sessionStorage.getItem('new_order_table');
    var table  = tableFromSession || 'N/A';
    var waiter = sessionStorage.getItem('new_order_waiter') || 'N/A';
    sessionStorage.removeItem('new_order_table');
    sessionStorage.removeItem('new_order_waiter');

    // If we arrived via back-navigation (no fresh table pick), restore the draft.
    var restoreOrder = null;
    if (!tableFromSession) {
        var _stored = sessionStorage.getItem('current_order');
        if (_stored) { try { restoreOrder = JSON.parse(_stored); } catch (_) {} }
    }
    if (restoreOrder) {
        table  = restoreOrder.table  || 'N/A';
        waiter = restoreOrder.waiter || 'N/A';
    }

    setTitle(table !== 'N/A' ? 'Tavolo: ' + table : 'Tavolo: N/A');
    setBack(null);

    _orderItems = cfg.items.map(function(it) { return Object.assign({}, it, { count: 0 }); });
    if (restoreOrder) {
        var _countMap = {};
        for (var _j = 0; _j < restoreOrder.menu.length; _j++) _countMap[restoreOrder.menu[_j].name] = restoreOrder.menu[_j].count || 0;
        for (var _k = 0; _k < _orderItems.length; _k++) { if (_countMap[_orderItems[_k].name]) _orderItems[_k].count = _countMap[_orderItems[_k].name]; }
    }

    var numCols = parseInt(gs('columns', '1'), 10) || 1;

    function itemsHtml() {
        return _orderItems.map(function(item, i) {
            if (item.kind === 'separator') {
                return '<div class="sep-row col-all"><strong>' + esc(item.name) + '</strong></div>';
            }
            return '<div class="item-row' + (item.count > 0 ? ' row-active' : '') + '" id="irow-' + i + '">' +
                '<div class="btn-group btn-group-sm">' +
                    '<button class="btn btn-danger minus" data-i="' + i + '">−</button>' +
                    '<button class="btn btn-default count-display" id="cnt-' + i + '" disabled>' + item.count + '</button>' +
                    '<button class="btn btn-success plus" data-i="' + i + '">+</button>' +
                '</div>' +
                '<span class="item-name">' + esc(item.name) + '</span>' +
                (item.price > 0 ? '<span class="item-price">€ ' + item.price.toFixed(2) + '</span>' : '') +
                '</div>';
        }).join('');
    }

    setContent(
        '<div class="new-order">' +
            '<div class="top-inputs">' +
                '<input type="text" id="inp-customer" class="form-control" placeholder="Nome cliente" value="' + esc(restoreOrder ? restoreOrder.customer || '' : '') + '">' +
                '<input type="text" id="inp-notes"    class="form-control" placeholder="Note"         value="' + esc(restoreOrder ? restoreOrder.notes    || '' : '') + '">' +
            '</div>' +
            '<div id="item-list" style="display:grid;grid-template-columns:repeat(' + numCols + ',1fr);gap:1px 2px">' + itemsHtml() + '</div>' +
        '</div>' +
        '<div class="bottom-bar">' +
            '<button id="btn-ok"   class="btn btn-primary">OK</button>' +
            '<button id="btn-back" class="btn btn-default">Indietro</button>' +
        '</div>'
    );

    $id('item-list').addEventListener('click', function(e) {
        var btn = e.target.closest ? e.target.closest('.count-btn') : null;
        if (!btn) { // IE fallback
            var t = e.target;
            if (t.classList && (t.classList.contains('minus') || t.classList.contains('plus'))) btn = t;
        }
        if (!btn) return;
        var i = parseInt(btn.getAttribute('data-i'));
        var delta = btn.classList.contains('plus') ? 1 : -1;
        _orderItems[i].count = Math.max(0, _orderItems[i].count + delta);
        $id('cnt-' + i).textContent = _orderItems[i].count;
        var row = $id('irow-' + i);
        if (row) {
            if (_orderItems[i].count > 0) row.classList.add('row-active');
            else row.classList.remove('row-active');
        }
    });

    $id('btn-ok').onclick = function() {
        var cashier  = gs('cashier') || 'N/A';
        var customer = $id('inp-customer').value.trim();
        var notes    = $id('inp-notes').value.trim();
        var order = { cashier: cashier, table: table, waiter: waiter,
                      customer: customer, notes: notes, menu: _orderItems };
        sessionStorage.setItem('current_order', JSON.stringify(order));
        navigate('#/order/preview');
    };

    $id('btn-back').onclick = function() { navigate(table !== 'N/A' ? '#/tables' : '#/'); };
}

async function screenShowOrder(orderId) {
    hideError();
    var cfg = await getMenuConfig();

    var order;
    if (orderId != null) {
        var data = await api.get('/orders/' + orderId + '/');
        order = data.order;
    } else {
        var stored = sessionStorage.getItem('current_order');
        if (!stored) { navigate('#/'); return; }
        order = JSON.parse(stored);
    }

    var isSaved = order.id != null;
    var isRist  = !cfg.is_sagra && !cfg.is_croce;
    var backDest = isSaved ? (sessionStorage.getItem('show_order_back') || (isRist ? '#/tables' : '#/')) : null;

    setTitle('Riepilogo ordine');
    setBack(backDest ? backDest : null);

    var receiptText = renderReceiptText(order, cfg);
    var receiptForPrint;
    if (cfg.is_sagra) {
        receiptForPrint = receiptText;
    } else {
        var sep = '\n\n\n' + '--------------------------------' + '\n\n\n';
        receiptForPrint = renderReceiptText(order, cfg, 'COPIA CLIENTE') +
                    sep +
                    renderReceiptText(order, cfg, 'COPIA CAMERIERE');
    }
    var total = computeTotal(order.menu);

    var filaHtml = '';
    if (cfg.is_sagra) {
        var fa = isFilaA(order.menu);
        filaHtml = '<span class="label ' + (fa ? 'label-info' : 'label-warning') + '" style="font-size:14px;padding:5px 10px">' + (fa ? 'Fila A' : 'Fila B') + '</span>';
    }

    var statusHtml = isSaved
        ? '<div class="alert alert-success" style="margin-top:10px;padding:8px 12px">Ordine #' + order.id + ' salvato</div>'
        : '<div class="alert alert-warning" style="margin-top:10px;padding:8px 12px">Non ancora inviato</div>';

    setContent(
        '<div class="show-order">' +
            '<div class="row" style="margin-bottom:10px;align-items:center">' +
                '<div class="col-xs-5">' + filaHtml + '</div>' +
                '<div class="col-xs-7 text-right"><strong class="h4" style="margin:0">Totale:&nbsp;' + total.toFixed(2) + '&nbsp;€</strong></div>' +
            '</div>' +
            '<div class="input-group" style="margin-bottom:12px">' +
                '<input type="number" id="inp-cash" class="form-control" placeholder="Denaro ricevuto" step="0.50" min="0">' +
                '<span class="input-group-addon" id="lbl-rest">Resto: 0.00</span>' +
            '</div>' +
            '<div class="panel panel-default" style="margin-bottom:0">' +
                '<div class="panel-body" style="padding:0"><pre class="receipt">' + esc(receiptText) + '</pre></div>' +
            '</div>' +
            statusHtml +
        '</div>' +
        '<div class="bottom-bar">' +
            '<button id="btn-save"    class="btn ' + (isSaved ? 'btn-default' : 'btn-success') + '">' + (isSaved ? 'Cibo' : 'Salva') + '</button>' +
            '<button id="btn-bar"     class="btn btn-default"' + (isSaved ? '' : ' disabled') + '>Bar</button>' +
            '<button id="btn-receipt" class="btn btn-default">Ricevuta</button>' +
            '<button id="btn-back"    class="btn btn-default">Indietro</button>' +
        '</div>'
    );

    $id('inp-cash').addEventListener('input', function(e) {
        var got  = parseFloat(e.target.value) || 0;
        var rest = got - total;
        $id('lbl-rest').textContent = 'Resto: ' + rest.toFixed(2);
    });

    $id('btn-save').onclick = async function() {
        disableBtn('btn-save', true);
        try {
            if (isSaved) {
                await api.post('/orders/' + order.id + '/print/', {});
            } else {
                var result = await api.post('/orders/', order);
                var saved = result.order;
                sessionStorage.removeItem('current_order');
                sessionStorage.setItem('show_order_back', isRist ? '#/tables' : '#/');
                // Auto-print receipt after saving, with the real order id/date.
                var sep = '\n\n\n' + '--------------------------------' + '\n\n\n';
                var savedPrintText = cfg.is_sagra
                    ? renderReceiptText(saved, cfg)
                    : renderReceiptText(saved, cfg, 'COPIA CLIENTE') + sep + renderReceiptText(saved, cfg, 'COPIA CAMERIERE');
                try { await printText(savedPrintText); } catch (pe) { showError(pe.message); }
                navigate('#/order/' + saved.id);
            }
        } catch (e) {
            showError(e.message);
            disableBtn('btn-save', false);
        }
    };

    $id('btn-bar').onclick = async function() {
        if (!isSaved) return;
        disableBtn('btn-bar', true);
        try {
            await api.post('/orders/' + order.id + '/print_drinks/', {});
        } catch (e) {
            showError(e.message);
        } finally {
            disableBtn('btn-bar', false);
        }
    };

    $id('btn-receipt').onclick = async function() {
        disableBtn('btn-receipt', true);
        try {
            await printText(receiptForPrint);
        } catch (e) {
            showError(e.message);
        } finally {
            disableBtn('btn-receipt', false);
        }
    };

    $id('btn-back').onclick = function() {
        if (backDest) navigate(backDest);
        else history.back();
    };
}

async function screenOrderList() {
    hideError();
    setTitle('Lista ordini');
    setBack('#/');
    setContent('<div class="loading">Caricamento...</div>');

    var orders = await api.get('/orders/');

    if (!orders.length) {
        setContent('<p class="empty-msg">Nessun ordine</p><div class="bottom-bar"><a href="#/" class="btn btn-default">Indietro</a></div>');
        return;
    }

    var rows = orders.map(function(o) {
        var date = o.date ? formatDateShort(o.date) : '';
        return '<a href="#/order/' + o.id + '" class="list-group-item order-item" onclick="sessionStorage.setItem(\'show_order_back\',\'#/orders\')">' +
            '<span class="badge">' + o.id + '</span>' +
            '<strong>' + esc(o.customer || '—') + '</strong> ' +
            '<small class="text-muted">' + esc(o.cashier || '') + ' ' + esc(o.table || '') + ' [' + esc(date) + ']</small>' +
            '</a>';
    }).join('');

    setContent(
        '<div class="list-group" style="margin-bottom:0">' + rows + '</div>' +
        '<div class="bottom-bar"><a href="#/" class="btn btn-default">Indietro</a></div>'
    );
}

async function screenTables() {
    hideError();
    setTitle('Mappa tavoli');
    setBack('#/');
    setContent('<div class="loading">Caricamento...</div>');

    var tables = await api.get('/tables/');
    var tableMap = {};
    for (var i = 0; i < tables.length; i++) tableMap[tables[i].name] = tables[i].waiter || '';

    var ROWS = 9, COLS = 3;
    var html = '<div class="tables-grid">';
    for (var row = 0; row < ROWS; row++) {
        for (var col = 0; col < COLS; col++) {
            var num = col * ROWS + row + 1;
            var name = String(num);
            var waiter = tableMap[name] || '';
            html += '<div class="table-cell' + (waiter ? ' table-busy' : '') + '" data-table="' + esc(name) + '" data-waiter="' + esc(waiter) + '">' +
                '<div class="table-num">' + num + '</div>' +
                (waiter ? '<div class="table-waiter">' + esc(waiter) + '</div>' : '') +
                '</div>';
        }
    }
    html += '</div>' +
        '<div class="bottom-bar"><a href="#/" class="btn btn-default">Indietro</a></div>';
    setContent(html);

    document.querySelectorAll('.table-cell').forEach(function(cell) {
        cell.addEventListener('click', function() {
            sessionStorage.setItem('new_order_table',  cell.getAttribute('data-table'));
            sessionStorage.setItem('new_order_waiter', cell.getAttribute('data-waiter'));
            navigate('#/order/new');
        });
    });
}

async function screenEditTables() {
    hideError();
    setTitle('Modifica tavoli');
    setBack('#/');
    setContent('<div class="loading">Caricamento...</div>');

    var tables = await api.get('/tables/');
    var currentWaiters = {};
    for (var i = 0; i < tables.length; i++) currentWaiters[tables[i].name] = tables[i].waiter || '';

    var ROWS = 9, COLS = 3;
    var gridHtml = '<div class="tables-grid edit-mode">';
    for (var row = 0; row < ROWS; row++) {
        for (var col = 0; col < COLS; col++) {
            var num = col * ROWS + row + 1;
            var name = String(num);
            var waiter = currentWaiters[name] || '';
            gridHtml += '<div class="table-cell" id="ec-' + num + '" data-table="' + esc(name) + '">' +
                '<div class="table-num">' + num + '</div>' +
                '<div class="table-waiter" id="ew-' + num + '">' + esc(waiter) + '</div>' +
                '</div>';
        }
    }
    gridHtml += '</div>';

    setContent(
        '<div class="edit-tables">' +
            '<div class="form-group">' +
                '<input type="text" id="inp-waiter" class="form-control" placeholder="Nome cameriere">' +
            '</div>' +
            gridHtml +
        '</div>' +
        '<div class="bottom-bar">' +
            '<button id="btn-save-t" class="btn btn-primary">Salva</button>' +
            '<a href="#/" class="btn btn-default">Annulla</a>' +
        '</div>'
    );

    document.querySelectorAll('.table-cell').forEach(function(cell) {
        cell.addEventListener('click', function() {
            var name   = cell.getAttribute('data-table');
            var num    = parseInt(name);
            var waiter = $id('inp-waiter').value.trim();
            currentWaiters[name] = waiter;
            var el = $id('ew-' + num);
            if (el) el.textContent = waiter;
        });
    });

    $id('btn-save-t').onclick = async function() {
        disableBtn('btn-save-t', true);
        try {
            var payload = Object.keys(currentWaiters).map(function(name) {
                return { name: name, waiter: currentWaiters[name] };
            });
            await api.put('/tables/', payload);
            navigate('#/');
        } catch (e) {
            showError(e.message);
            disableBtn('btn-save-t', false);
        }
    };
}

// ─── Router ──────────────────────────────────────────────────────────────────

async function route() {
    var hash  = location.hash || '#/';
    var path  = hash.slice(1).split('?')[0];
    var parts = path.split('/').filter(Boolean);

    // scroll to top on navigation
    window.scrollTo(0, 0);
    hideError();

    try {
        if (parts.length === 0) {
            await screenMain();
        } else if (parts[0] === 'settings') {
            await screenSettings();
        } else if (parts[0] === 'order' && parts[1] === 'new') {
            await screenNewOrder();
        } else if (parts[0] === 'order' && parts[1] === 'preview') {
            await screenShowOrder(null);
        } else if (parts[0] === 'order' && parts[1]) {
            await screenShowOrder(parseInt(parts[1], 10));
        } else if (parts[0] === 'orders') {
            await screenOrderList();
        } else if (parts[0] === 'tables' && parts[1] === 'edit') {
            await screenEditTables();
        } else if (parts[0] === 'tables') {
            await screenTables();
        } else {
            await screenMain();
        }
    } catch (e) {
        showError('Errore: ' + e.message);
        console.error(e);
    }
}

// ─── Init ─────────────────────────────────────────────────────────────────────

window.addEventListener('hashchange', route);
window.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' || e.keyCode === 27) {
        var top = $id('back-btn');
        if (top && top.style.display !== 'none' && top.onclick) { top.onclick(); return; }
        var bot = $id('btn-back');
        if (bot && bot.onclick) bot.onclick();
    }
});
window.addEventListener('DOMContentLoaded', function() {
    updateDevBadge();
    route();
});
