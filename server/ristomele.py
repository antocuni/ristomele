import os
import py
import json
import flask
from flask import current_app
from server import config

TMPDIR = py.path.local.mkdtemp()
STATIC = config.ROOT.join('server', 'static')
ristomele = flask.Blueprint('ristomele', __name__)

def error(message, status=403):
    myjson = flask.jsonify(result='error',
                           message=message)
    return myjson, status

def topdf(html, basename, htmldir, pdfdir):
    htmlname = htmldir.join(basename + '.html')
    pdfname = pdfdir.join(basename + '.pdf')
    with htmlname.open('w') as f:
        f.write(html.encode('utf8'))
    cmdline = 'wkhtmltopdf "%s" "%s"' % (htmlname, pdfname)
    print cmdline
    ret = os.system(cmdline)
    if ret != 0:
        raise ValueError('Error when executing wkhtmltopdf')
    return pdfname

def split_columns(menu):
    items = menu['items']
    n = len(items)/2
    columns = [
        items[:n],
        items[n:],
    ]
    return columns


@ristomele.route('/orders/', methods=['POST'])
def new_order():
    from server import model
    menu = flask.request.json
    if menu is None:
        return error('Expected JSON request', 400)
    #
    current_app.logger.info('\norder POST: %s' % menu)
    #
    myorder = model.Order(menu=json.dumps(menu))
    model.db.session.add(myorder)
    model.db.session.commit()
    html = flask.render_template('order.html',
                                 static=str(STATIC),
                                 order=myorder,
                                 menu=menu,
                                 columns=split_columns(menu))
    #
    # we generate the HTML in a temporary dir, but the PDF into a
    # spooldir: the idea is that we will have a deamon which prints all
    # the PDFs which are copied there
    pdf = topdf(html, 'order_%06d' % myorder.id, TMPDIR,
                current_app.config['SPOOLDIR'])
    if not current_app.config['TESTING']:
        os.system('evince "%s" &' % pdf)
    return flask.jsonify(result='OK', order=myorder.as_dict())


@ristomele.route('/orders/', methods=['GET'])
def all_orders():
    from server import model
    orders = model.Order.query.order_by(model.Order.id.desc()).all()
    orders = [order.as_dict() for order in orders]
    return flask.jsonify(orders)
