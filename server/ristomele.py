import os
import time
from datetime import datetime
import py
import json
from collections import Counter, defaultdict
import flask
from flask import current_app
from server import config
from server import escpos

# To switch between "sagra" and "ristorante" mode, modify config.py


# apparently, if you use a long cable, /dev/usb/lp-thermal gets disconnected
# from time to time and loses the first chars of a print. We this hack, we
# print enough whitespace at the beginning so that even if some chars are
# lost, the receipt is still readable. The cost is some wasted paper :(
LONG_CABLE_HACK = 0
#LONG_CABLE_HACK = 200

# if True, we print using PDF and laser printer. Else, we print a small
# receipt
USE_PDF_FOR_FOOD = False


STATIC = config.ROOT.join('server', 'static')
ristomele = flask.Blueprint('ristomele', __name__)

def spooldir_for(kind):
    d = current_app.config['SPOOLDIR'].join(kind)
    return d.ensure(dir=True)

def error(message, status=403):
    myjson = flask.jsonify(result='error',
                           message=message)
    return myjson, status

def split_columns(items):
    n = len(items)/2
    columns = [
        items[:n],
        items[n:],
    ]
    return columns

@ristomele.route('/apk/', methods=['GET'])
def get_apk():
    apk = config.ROOT.join('mobile', 'bin', 'RistoMele-0.1-debug.apk')
    return flask.send_file(str(apk), as_attachment=True)


@ristomele.route('/orders/', methods=['POST'])
def new_order():
    from server import model
    order_dict = flask.request.json
    if order_dict is None:
        return error('Expected JSON request', 400)
    #
    current_app.logger.info('\norder POST: %s' % order_dict)
    #
    #myorder = model.Order(date=datetime.now(), menu=json.dumps(menu))
    myorder = model.Order.from_dict(order_dict)
    model.db.session.add(myorder)
    model.db.session.commit()
    do_print_order(myorder)
    do_print_drinks(myorder)
    return flask.jsonify(result='OK', order=myorder.as_dict())


@ristomele.route('/orders/<int:order_id>/print/', methods=['GET', 'POST'])
def reprint_order(order_id):
    from server import model
    myorder = model.Order.query.get(order_id)
    if myorder is None:
        return error("Cannot find the requested order")
    do_print_order(myorder, reprint=True)
    return flask.jsonify(result='OK')

@ristomele.route('/orders/<int:order_id>/', methods=['GET'])
def get_order(order_id):
    from server import model
    myorder = model.Order.query.get(order_id)
    if myorder is None:
        return error("Cannot find the requested order")
    return flask.jsonify(result='OK', order=myorder.as_dict())


@ristomele.route('/orders/<int:order_id>/print_drinks/', methods=['POST'])
def print_drinks_order(order_id):
    from server import model
    myorder = model.Order.query.get(order_id)
    if myorder is None:
        return error("Cannot find the requested order")
    do_print_drinks(myorder)
    return flask.jsonify(result='OK')

def filter_menu(menu):
    res = []
    for item in menu:
        if item['kind'] == 'item' and item['count'] == 0:
            continue
        res.append(item)
    return res

def do_print_order(myorder, reprint=False):
    if USE_PDF_FOR_FOOD:
        assert False, 'uncomment do_print_order_pdf'
        #do_print_order_pdf(myorder, reprint)
    else:
        do_print_order_lp(myorder, reprint)

def do_print_order_lp(myorder, reprint=False):
    """
    Print the order using a thermal printer
    """
    receipt = myorder.food_receipt(reprint=reprint)
    if receipt is None:
        return # no food, no receipt
    #
    receipt = escpos.magic_encode(receipt)
    txt = spooldir_for('food').join('order_%06d.txt' % myorder.id)
    with txt.open('wb') as f:
        f.write(receipt)


## def do_print_order_pdf(myorder, reprint=False):
##     """
##     print the order using PDF/laser printer
##     """
##     menu = json.loads(myorder.menu)
##     menu = filter_menu(menu)
##     html = flask.render_template('order.html',
##                                  static=str(STATIC),
##                                  reprint=reprint,
##                                  order=myorder,
##                                  columns=split_columns(menu))
##     #
##     html_file = spooldir_for('orders').join('order_%06d.html' % myorder.id)
##     with html_file.open('wb') as f:
##         f.write(html.encode('utf8'))
##     #
##     # XXX: reimplement the evince preview functionality


def do_print_drinks(myorder):
    receipt = myorder.drink_receipt()
    if receipt is None:
        return # no drinks, no receipt
    #
    receipt = escpos.magic_encode(receipt)
    if LONG_CABLE_HACK:
        receipt = ' '*LONG_CABLE_HACK + '\n' + receipt
    txt = spooldir_for('drinks').join('order_%06d.txt' % myorder.id)
    with txt.open('wb') as f:
        f.write(receipt)

@ristomele.route('/orders/', methods=['GET'])
def all_orders():
    from server import model
    orders = model.Order.query.order_by(model.Order.id.desc()).all()
    orders = [order.as_dict_light() for order in orders]
    return flask.jsonify(orders)

def _update_one_table(name, waiter):
    from server import model
    table = model.Table.query.get(name)
    if table is None:
        # no table with this name, create one from scratch
        table = model.Table(name=name, waiter=waiter)
    else:
        table.waiter = waiter
    model.db.session.add(table)
    return table

@ristomele.route('/tables/<name>/', methods=['PUT'])
def update_table(name):
    from server import model
    waiter = flask.request.json['waiter']
    table = _update_one_table(name, waiter)
    model.db.session.commit()
    return flask.jsonify(table.as_dict())

@ristomele.route('/tables/', methods=['GET'])
def all_tables():
    from server import model
    tables = model.Table.query.all()
    tables = [t.as_dict() for t in tables]
    return flask.jsonify(tables)

@ristomele.route('/tables/', methods=['PUT'])
def update_many_tables():
    from server import model
    tables = []
    for tdict in flask.request.json:
        name = tdict['name']
        waiter = tdict['waiter']
        tables.append(_update_one_table(name, waiter))
    #
    model.db.session.commit()
    tables = [t.as_dict() for t in tables]
    return flask.jsonify(tables)


@ristomele.route('/timestamp/', methods=['GET', 'POST'])
def timestamp():
    if flask.request.method == 'POST':
        timestamp = flask.request.json['timestamp']
        timestamp = float(timestamp)
        ret = os.system('sudo date -s @%s' % timestamp)
        if ret != 0:
            return error("Cannot set the date")
    return flask.jsonify(result='OK',
                         timestamp=time.time())

@ristomele.route('/stats/', methods=['GET'])
def stats():
    from server import model
    hide_money = 'hide_money' in flask.request.args
    show_money = not hide_money
    #
    total_money = Counter()
    total_orders = Counter()
    total_foc = Counter()
    by_cashier = defaultdict(Counter)
    by_item = defaultdict(Counter)
    orders = model.Order.query.all()
    for order in orders:
        #dt = order.date.date()
        dt = order.date_dwim
        total_orders[dt] += 1
        total_money[dt] += order.get_total()
        by_cashier[dt][order.cashier] += 1
        #
        item_counter = by_item[dt]
        item_counter['Ordini'] += 1
        menu = json.loads(order.menu)
        for item in menu:
            if item['kind'] != 'item':
                continue
            item_counter[item['name']] += item['count']
            if item['name'].startswith('Foc. '):
                total_foc[dt] += item['count']
    #
    return flask.render_template('stats.html',
                                 sorted=sorted,
                                 show_money=show_money,
                                 by_item=by_item,
                                 by_cashier=by_cashier,
                                 total_orders=total_orders,
                                 total_foc=total_foc,
                                 total_money=total_money)

@ristomele.route('/static/bootstrap.min.css', methods=['GET'])
def send_static():
    css = config.ROOT.join('server', 'static', 'bootstrap.min.css')
    return flask.send_file(str(css))
