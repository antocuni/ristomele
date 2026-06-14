# -*- coding: utf-8 -*-
"""
Advanced statistics for RistoMele.
Usage: python -m server.stats [--db PATH] [--html OUTPUT.html]
"""
from __future__ import print_function
import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import date as date_type, datetime, timedelta

CHART_VERSION = '4.4.4'
CHART_CDN_URL = 'https://cdn.jsdelivr.net/npm/chart.js@{v}/dist/chart.umd.min.js'.format(v=CHART_VERSION)
CHART_LOCAL_PATH = '/static/chart.umd.{v}.min.js'.format(v=CHART_VERSION)

BIN_MINUTES = 30

DAYS_IT = [u'Lunedì', u'Martedì', u'Mercoledì', u'Giovedì', u'Venerdì', u'Sabato', u'Domenica']


def _parse_dt(s):
    return datetime.strptime(s.split('.')[0], '%Y-%m-%d %H:%M:%S')


def _date_dwim(dt):
    return (dt - timedelta(hours=3)).date()


def _slot(dt):
    """Return a datetime truncated to BIN_MINUTES boundary (the real datetime, no offset)."""
    total = dt.hour * 60 + dt.minute
    rounded = total // BIN_MINUTES * BIN_MINUTES
    return dt.replace(hour=rounded // 60, minute=rounded % 60, second=0, microsecond=0)


def _slot_range(min_slot, max_slot):
    """Return sorted list of slot datetimes from min to max."""
    result = []
    current = min_slot
    while current <= max_slot:
        result.append(current)
        current = current + timedelta(minutes=BIN_MINUTES)
    return result


def _slot_labels(slots):
    """Format slot datetimes as HH:MM for chart display.
    Order is correct because slots are sorted datetimes; date is omitted for readability."""
    return [s.strftime('%H:%M') for s in slots]


def load_data(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    orders = conn.execute('SELECT id, date, menu FROM "order" ORDER BY date').fetchall()
    deliveries = conn.execute('SELECT order_id, delivery_time FROM delivery').fetchall()
    conn.close()
    return orders, deliveries


def _estimate_delivery_times(orders_for_day, delivery_map):
    """
    For orders without a delivery record, estimate delivery time as the
    minimum delivery time of all higher-id orders that have a record.
    Rationale: if order N was served, all orders < N should have been served too.
    Out-of-order deliveries are handled by taking the min (optimistic bound).
    Returns {order_id -> estimated_delivery_dt} for all estimable orders.
    """
    sorted_orders = sorted(orders_for_day, key=lambda o: o['id'])
    result = {}
    min_future_dt = None
    for order in reversed(sorted_orders):
        oid = order['id']
        if oid in delivery_map:
            dt = delivery_map[oid]
            result[oid] = dt
            min_future_dt = dt if min_future_dt is None else min(min_future_dt, dt)
        elif min_future_dt is not None:
            result[oid] = min_future_dt
    return result


def compute_stats(orders, deliveries):
    delivery_map = {d['order_id']: _parse_dt(d['delivery_time']) for d in deliveries}

    # {day -> {slot -> {orders, foc}}}
    by_slot = defaultdict(lambda: defaultdict(lambda: {'orders': 0, 'foc': 0}))
    # {day -> {n_foc -> n_orders}}
    foc_distribution = defaultdict(lambda: defaultdict(int))
    total_orders = defaultdict(int)
    total_foc = defaultdict(int)
    # {day -> list of order rows} — collected for delivery estimation
    orders_by_day = defaultdict(list)

    for order in orders:
        if not order['date'] or not order['menu']:
            continue
        dt = _parse_dt(order['date'])
        day = _date_dwim(dt)
        slot = _slot(dt)
        menu = json.loads(order['menu'])
        foc = sum(
            item['count'] for item in menu
            if item['kind'] == 'item'
            and not item['is_drink']
            and item['name'].startswith('Foc. ')
        )
        by_slot[day][slot]['orders'] += 1
        by_slot[day][slot]['foc'] += foc
        foc_distribution[day][foc] += 1
        total_orders[day] += 1
        total_foc[day] += foc
        orders_by_day[day].append(order)

    # Build estimated delivery intervals per day using best-effort heuristic.
    # Also track first *actual* delivery per day to clip the chart start,
    # and bucket focaccini by estimated delivery slot.
    intervals_by_day = {}
    first_actual_delivery_by_day = {}
    # {day -> {slot_datetime -> foc_count}} bucketed by estimated delivery time
    foc_delivered_by_slot = defaultdict(lambda: defaultdict(int))
    for day, day_orders in orders_by_day.items():
        estimated = _estimate_delivery_times(day_orders, delivery_map)
        intervals = []
        for order in day_orders:
            if not order['date']:
                continue
            o_dt = _parse_dt(order['date'])
            d_dt = estimated.get(order['id'])
            if d_dt is not None:
                intervals.append((o_dt, d_dt))
                menu = json.loads(order['menu'])
                foc = sum(
                    item['count'] for item in menu
                    if item['kind'] == 'item'
                    and not item['is_drink']
                    and item['name'].startswith('Foc. ')
                )
                foc_delivered_by_slot[day][_slot(d_dt)] += foc
            if order['id'] in delivery_map:
                actual = delivery_map[order['id']]
                prev = first_actual_delivery_by_day.get(day)
                if prev is None or actual < prev:
                    first_actual_delivery_by_day[day] = actual
        intervals_by_day[day] = intervals

    # queue depth: for each slot boundary, count in-flight orders.
    # Only include slots from the first actual delivery onward (before that
    # we have no delivery records so the estimate is meaningless).
    # {day -> {slot_datetime -> depth}}
    queue_depth = {}
    for day, intervals in intervals_by_day.items():
        all_slots = sorted(by_slot[day].keys())
        if not all_slots:
            continue
        first_delivery = first_actual_delivery_by_day.get(day)
        depth_by_slot = {}
        for slot_dt in _slot_range(min(all_slots), max(all_slots)):
            if first_delivery is not None and slot_dt < first_delivery:
                continue
            depth_by_slot[slot_dt] = sum(
                1 for (o_dt, d_dt) in intervals if o_dt <= slot_dt < d_dt
            )
        queue_depth[day] = depth_by_slot

    return {
        'by_slot': by_slot,
        'foc_delivered_by_slot': foc_delivered_by_slot,
        'first_actual_delivery_by_day': first_actual_delivery_by_day,
        'foc_distribution': foc_distribution,
        'queue_depth': queue_depth,
        'delivery_map': delivery_map,
        'total_orders': total_orders,
        'total_foc': total_foc,
    }


# ── HTML generation ────────────────────────────────────────────────────────────

def _day_label(day):
    return '{dow} {date}'.format(dow=DAYS_IT[day.weekday()], date=day.strftime('%d/%m/%Y'))


def _section_orders_by_slot(day, day_slots, stats, chart_id):
    all_slots = sorted(day_slots.keys())
    if not all_slots:
        return '', ''
    slot_range = _slot_range(min(all_slots), max(all_slots))
    labels = _slot_labels(slot_range)
    orders_data = [day_slots.get(s, {}).get('orders', 0) for s in slot_range]
    foc_ord_data = [day_slots.get(s, {}).get('foc', 0) for s in slot_range]
    foc_del_slots = stats['foc_delivered_by_slot'][day]
    first_delivery = stats['first_actual_delivery_by_day'].get(day)
    foc_del_data = [
        foc_del_slots.get(s, 0) if first_delivery is None or s >= first_delivery else None
        for s in slot_range
    ]

    cid = 'chart-slot-{i}'.format(i=chart_id)
    html = (
        '\n      <h3>Ordini e focaccini per fascia oraria (30 min)</h3>'
        '\n      <div class="chart-wrap"><canvas id="{cid}"></canvas></div>'
    ).format(cid=cid)

    js = (
        '\n    new Chart(document.getElementById({cid}), {{'
        '\n      type: "bar",'
        '\n      data: {{'
        '\n        labels: {labels},'
        '\n        datasets: ['
        '\n          {{'
        '\n            label: "Ordini",'
        '\n            data: {orders},'
        '\n            backgroundColor: "rgba(39, 174, 96, 0.7)",'
        '\n            yAxisID: "y",'
        '\n          }},'
        '\n          {{'
        '\n            label: "Foc. ordinati",'
        '\n            data: {foc_ord},'
        '\n            type: "line",'
        '\n            borderColor: "rgba(231, 76, 60, 0.9)",'
        '\n            backgroundColor: "rgba(0,0,0,0)",'
        '\n            yAxisID: "y2",'
        '\n            tension: 0.3,'
        '\n          }},'
        '\n          {{'
        '\n            label: "Foc. consegnati (stimati)",'
        '\n            data: {foc_del},'
        '\n            type: "line",'
        '\n            borderColor: "rgba(52, 152, 219, 0.9)",'
        '\n            backgroundColor: "rgba(52, 152, 219, 0.1)",'
        '\n            yAxisID: "y2",'
        '\n            tension: 0.3,'
        '\n            fill: true,'
        '\n          }}'
        '\n        ]'
        '\n      }},'
        '\n      options: {{'
        '\n        responsive: true,'
        '\n        maintainAspectRatio: false,'
        '\n        interaction: {{ mode: "index", intersect: false }},'
        '\n        scales: {{'
        '\n          y: {{ beginAtZero: true, title: {{ display: true, text: "Ordini" }} }},'
        '\n          y2: {{'
        '\n            beginAtZero: true,'
        '\n            position: "right",'
        '\n            title: {{ display: true, text: "Focaccini" }},'
        '\n            grid: {{ drawOnChartArea: false }}'
        '\n          }}'
        '\n        }}'
        '\n      }}'
        '\n    }});'
    ).format(
        cid=json.dumps(cid),
        labels=json.dumps(labels),
        orders=json.dumps(orders_data),
        foc_ord=json.dumps(foc_ord_data),
        foc_del=json.dumps(foc_del_data),
    )
    return html, js


def _section_foc_distribution(day, dist, chart_id):
    if not dist:
        return '', ''
    max_foc = max(dist.keys())
    labels = list(range(0, max_foc + 1))
    counts = [dist.get(n, 0) for n in labels]
    total = sum(counts)
    mean = sum(n * c for n, c in zip(labels, counts)) / float(total) if total else 0

    cid = 'chart-dist-{i}'.format(i=chart_id)
    html = (
        '\n      <h3>Distribuzione focaccini per ordine (media: {mean:.1f})</h3>'
        '\n      <div class="chart-wrap chart-wrap-sm"><canvas id="{cid}"></canvas></div>'
    ).format(mean=mean, cid=cid)

    js = (
        '\n    new Chart(document.getElementById({cid}), {{'
        '\n      type: "bar",'
        '\n      data: {{'
        '\n        labels: {labels},'
        '\n        datasets: [{{'
        '\n          label: "Ordini",'
        '\n          data: {counts},'
        '\n          backgroundColor: "rgba(142, 68, 173, 0.7)",'
        '\n        }}]'
        '\n      }},'
        '\n      options: {{'
        '\n        responsive: true,'
        '\n        maintainAspectRatio: false,'
        '\n        plugins: {{ legend: {{ display: false }} }},'
        '\n        scales: {{'
        '\n          x: {{ title: {{ display: true, text: "Focaccini per ordine" }} }},'
        u'\n          y: {{ beginAtZero: true, title: {{ display: true, text: "N° ordini" }} }}'
        '\n        }}'
        '\n      }}'
        '\n    }});'
    ).format(
        cid=json.dumps(cid),
        labels=json.dumps(labels),
        counts=json.dumps(counts),
    )
    return html, js


def _section_queue_depth(day, depth_by_slot, chart_id):
    if not depth_by_slot:
        return '', ''
    all_slots = sorted(depth_by_slot.keys())
    slot_range = _slot_range(min(all_slots), max(all_slots))
    labels = _slot_labels(slot_range)
    depths = [depth_by_slot.get(s, 0) for s in slot_range]
    peak = max(depths) if depths else 0

    cid = 'chart-queue-{i}'.format(i=chart_id)
    html = (
        u'\n      <h3>Ordini in coda (picco: {peak})</h3>'
        u'\n      <div class="chart-wrap chart-wrap-sm"><canvas id="{cid}"></canvas></div>'
    ).format(peak=peak, cid=cid)

    js = (
        '\n    new Chart(document.getElementById({cid}), {{'
        '\n      type: "line",'
        '\n      data: {{'
        '\n        labels: {labels},'
        '\n        datasets: [{{'
        '\n          label: "Ordini in coda",'
        '\n          data: {depths},'
        '\n          borderColor: "rgba(230, 126, 34, 0.9)",'
        '\n          backgroundColor: "rgba(230, 126, 34, 0.15)",'
        '\n          tension: 0.3,'
        '\n          fill: true,'
        '\n        }}]'
        '\n      }},'
        '\n      options: {{'
        '\n        responsive: true,'
        '\n        maintainAspectRatio: false,'
        '\n        plugins: {{ legend: {{ display: false }} }},'
        '\n        scales: {{'
        '\n          x: {{ title: {{ display: true, text: "Orario" }} }},'
        '\n          y: {{ beginAtZero: true, title: {{ display: true, text: "Ordini in coda" }} }}'
        '\n        }}'
        '\n      }}'
        '\n    }});'
    ).format(
        cid=json.dumps(cid),
        labels=json.dumps(labels),
        depths=json.dumps(depths),
    )
    return html, js


def generate_html(db_path, cdn=False):
    orders, deliveries = load_data(db_path)
    stats = compute_stats(orders, deliveries)
    by_slot = stats['by_slot']
    foc_dist = stats['foc_distribution']
    chart_src = CHART_CDN_URL if cdn else CHART_LOCAL_PATH

    sections = []
    chart_inits = []

    queue_depth = stats['queue_depth']

    for i, day in enumerate(sorted(by_slot.keys(), reverse=True)):
        html1, js1 = _section_orders_by_slot(day, by_slot[day], stats, i)
        html2, js2 = _section_foc_distribution(day, foc_dist[day], i)
        html3, js3 = _section_queue_depth(day, queue_depth.get(day, {}), i)
        n_orders = stats['total_orders'][day]
        n_foc = stats['total_foc'][day]
        day_block = (
            '\n    <section class="day-section">'
            '\n      <h2>{day} &ndash; {n} ordini, {f} focaccini</h2>'
            '{slot}{dist}{queue}'
            '\n    </section>'
        ).format(
            day=_day_label(day), n=n_orders, f=n_foc,
            slot=html1, dist=html2, queue=html3,
        )
        sections.append(day_block)
        chart_inits.append(js1)
        chart_inits.append(js2)
        chart_inits.append(js3)

    body = ''.join(sections) if sections else '<p style="padding:20px">Nessun dato.</p>'

    return u'''<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Statistiche avanzate – RistoMele</title>
  <script src="{chart_src}"></script>
  <style>
    body {{ font-family: sans-serif; background: #f5f5f5; margin: 0; padding: 0; }}
    header {{ background: #2c3e50; color: #fff; padding: 14px 24px; }}
    header h1 {{ margin: 0; font-size: 22px; }}
    .content {{ max-width: 960px; margin: 0 auto; padding: 16px; }}
    .day-section {{
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.12);
      margin: 20px 0;
      padding: 16px 20px;
    }}
    .day-section h2 {{ margin: 0 0 14px; font-size: 18px; color: #2c3e50; }}
    .day-section h3 {{
      margin: 0 0 8px;
      font-size: 12px;
      color: #777;
      text-transform: uppercase;
      letter-spacing: .5px;
    }}
    .chart-wrap {{ position: relative; height: 300px; }}
    .chart-wrap-sm {{ position: relative; height: 200px; margin-top: 20px; }}
  </style>
</head>
<body>
<header><h1>Statistiche avanzate – RistoMele</h1></header>
<div class="content">
  {body}
</div>
<script>
{js}
</script>
</body>
</html>'''.format(chart_src=chart_src, body=body, js=''.join(chart_inits))


# ── Text summary ───────────────────────────────────────────────────────────────

def print_summary(db_path):
    orders, deliveries = load_data(db_path)
    stats = compute_stats(orders, deliveries)

    print('Database: {0}'.format(db_path))
    print('')
    for day in sorted(stats['total_orders'].keys(), reverse=True):
        n = stats['total_orders'][day]
        f = stats['total_foc'][day]
        ratio = float(f) / n if n else 0
        print('{day}:'.format(day=_day_label(day)))
        print('  Ordini:    {0}'.format(n))
        print('  Focaccini: {0}  ({1:.1f} per ordine)'.format(f, ratio))
        print('')


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=u'RistoMele — statistiche avanzate')
    parser.add_argument('--db', default='db.sqlite', help='Percorso database SQLite')
    parser.add_argument('--html', help='Salva report HTML in questo file')
    args = parser.parse_args()

    print_summary(args.db)

    if args.html:
        html = generate_html(args.db, cdn=True)
        with open(args.html, 'w') as f:
            f.write(html.encode('utf-8'))
        print('Report HTML salvato in: {0}'.format(args.html))
