import os
import py
import json
import flask
from flask import current_app
from server import config

STATIC = config.ROOT.join('server', 'static')
ristomele = flask.Blueprint('ristomele', __name__)

def error(message, status=403):
    myjson = flask.jsonify(result='error',
                           message=message)
    return myjson, status

def topdf(html, basename):
    tmpdir = py.path.local.mkdtemp()
    htmlname = tmpdir.join(basename + '.html')
    with htmlname.open('w') as f:
        f.write(html.encode('utf8'))
    pdfname = htmlname.new(ext='pdf')
    cmdline = 'wkhtmltopdf "%s" "%s"' % (htmlname, pdfname)
    print cmdline
    ret = os.system(cmdline)
    if ret != 0:
        raise ValueError('Error when executing wkhtmltopdf')
    return pdfname

@ristomele.route('/order/', methods=['GET', 'POST'])
def order():
    from server import model
    if flask.request.method == 'POST':
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
                                     menu=menu)
        pdf = topdf(html, 'order')
        if not current_app.config['TESTING']:
            # XXX: eventually, we should print it and/or move it to a spool dir
            os.system('evince "%s" &' % pdf)
        return flask.jsonify(result='OK')
    else:
        return error('Only POST allowed', None, 405)
