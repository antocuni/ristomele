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
    var CHUNK = 512;
    for (var i = 0; i < data.length; i += CHUNK) {
        await chr.writeValue(data.slice(i, i + CHUNK));
    }
}

async function blePrintText(text) {
    if (!navigator.bluetooth) throw new Error('Web Bluetooth non supportato. Usa Chrome/Edge su Android o desktop.');
    var deviceName = gs('ble_device_name');
    if (!deviceName) throw new Error('Nessuna stampante configurata. Vai in Impostazioni e seleziona una stampante.');

    var device = await navigator.bluetooth.requestDevice({
        filters: [{ name: deviceName }],
        optionalServices: PRINTER_SERVICES,
    });
    var server = await device.gatt.connect();
    var chr = await findPrintChar(server);
    if (!chr) { server.disconnect(); throw new Error('Caratteristica di stampa non trovata sulla stampante.'); }

    var enc = new TextEncoder();
    await chr.writeValue(new Uint8Array([0x1B, 0x40])); // ESC @ init
    await bleWriteChunked(chr, enc.encode(text));
    await chr.writeValue(new Uint8Array([0x0A, 0x0A, 0x0A, 0x0A, 0x0A])); // feed
    try { await chr.writeValue(new Uint8Array([0x1D, 0x56, 0x00])); } catch (_) {} // cut
    server.disconnect();
}

async function bleSelectPrinter() {
    if (!navigator.bluetooth) throw new Error('Web Bluetooth non supportato in questo browser.');
    var device = await navigator.bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: PRINTER_SERVICES,
    });
    ss('ble_device_name', device.name);
    return device.name;
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

function showError(msg) {
    var bar = document.getElementById('error-bar');
    document.getElementById('error-msg').textContent = msg;
    bar.style.display = 'flex';
}

function hideError() {
    document.getElementById('error-bar').style.display = 'none';
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
    document.getElementById('dev-badge').style.display = gs('dev_mode') === '1' ? '' : 'none';
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

    var cashier = gs('cashier');
    var devMode = gs('dev_mode') === '1';
    var bleDevice = gs('ble_device_name') || '(nessuna)';
    var cols = gs('columns', '1');

    var serverTimeHtml = '<em>caricamento...</em>';

    setContent(
        '<div class="settings-form">' +
            '<div class="form-group">' +
                '<label>Nome cassiere</label>' +
                '<input type="text" id="inp-cashier" class="form-control" value="' + esc(cashier) + '">' +
            '</div>' +
            '<div class="form-group">' +
                '<label>Stampante BLE</label>' +
                '<div class="input-group">' +
                    '<span class="input-group-addon" id="ble-name">' + esc(bleDevice) + '</span>' +
                    '<span class="input-group-btn">' +
                        '<button id="btn-ble" class="btn btn-default" type="button">Seleziona</button>' +
                    '</span>' +
                '</div>' +
            '</div>' +
            '<div class="form-group">' +
                '<label>Colonne menu</label>' +
                '<select id="sel-columns" class="form-control">' +
                    '<option value="1"' + (cols === '1' ? ' selected' : '') + '>1 colonna</option>' +
                    '<option value="2"' + (cols === '2' ? ' selected' : '') + '>2 colonne</option>' +
                    '<option value="3"' + (cols === '3' ? ' selected' : '') + '>3 colonne</option>' +
                '</select>' +
            '</div>' +
            '<div class="form-group">' +
                '<div class="checkbox"><label>' +
                    '<input type="checkbox" id="chk-dev" ' + (devMode ? 'checked' : '') + '> ' +
                    'Modalità sviluppo (stampa in console)' +
                '</label></div>' +
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
        ss('cashier', $id('inp-cashier').value.trim());
        ss('columns', $id('sel-columns').value);
        ss('dev_mode', $id('chk-dev').checked ? '1' : '0');
        updateDevBadge();
        navigate('#/');
    };

    $id('btn-ble').onclick = async function() {
        disableBtn('btn-ble', true);
        try {
            var name = await bleSelectPrinter();
            $id('ble-name').textContent = name;
        } catch (e) {
            showError(e.message);
        } finally {
            disableBtn('btn-ble', false);
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

    var table  = sessionStorage.getItem('new_order_table')  || 'N/A';
    var waiter = sessionStorage.getItem('new_order_waiter') || 'N/A';
    sessionStorage.removeItem('new_order_table');
    sessionStorage.removeItem('new_order_waiter');

    setTitle(table !== 'N/A' ? 'Tavolo: ' + table : 'Tavolo: N/A');
    setBack(null);

    _orderItems = cfg.items.map(function(it) { return Object.assign({}, it, { count: 0 }); });

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
                '<input type="text" id="inp-customer" class="form-control" placeholder="Nome cliente">' +
                '<input type="text" id="inp-notes"    class="form-control" placeholder="Note">' +
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
    var printText;
    if (cfg.is_sagra) {
        printText = receiptText + '\n.\n.\n.';
    } else {
        var sep = '\n\n\n' + '--------------------------------' + '\n\n\n';
        printText = renderReceiptText(order, cfg, 'COPIA CLIENTE') +
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
                sessionStorage.setItem('show_order_back', isRist ? '#/tables' : '#/');
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
        if (gs('dev_mode') === '1') {
            console.log('=== RICEVUTA ===\n' + printText);
            return;
        }
        if (!navigator.bluetooth) {
            showError('Web Bluetooth non supportato. Usa Chrome su Android o Chrome/Edge desktop.');
            return;
        }
        disableBtn('btn-receipt', true);
        try {
            await blePrintText(printText);
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
            '<small class="text-muted">' + esc(o.table || '') + ' [' + esc(date) + ']</small>' +
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
window.addEventListener('DOMContentLoaded', function() {
    updateDevBadge();
    route();
});
