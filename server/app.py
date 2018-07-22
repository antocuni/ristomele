import os
import py
import json
import flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename
from server import config
from server import srczip

app = flask.Flask('risto_server', root_path='server')
STATIC = config.ROOT.join('server', 'static')
MOBILE = config.ROOT.join('mobile')
DB = config.ROOT.join('db.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % DB

db = SQLAlchemy(app)
from server import model
db.create_all()

srczip.add_routes(app)


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

@app.route('/order/', methods=['GET', 'POST'])
def order():
    if flask.request.method == 'POST':
        menu = flask.request.json
        if menu is None:
            return error('Expected JSON request', 400)
        #
        app.logger.info('\norder POST: %s' % menu)
        #
        myorder = model.Order(menu=json.dumps(menu))
        db.session.add(myorder)
        db.session.commit()
        html = flask.render_template('order.html',
                                     static=str(STATIC),
                                     order=myorder,
                                     menu=menu)
        pdf = topdf(html, 'order')
        # XXX: eventually, we should print it and/or move it to a spool dir
        os.system('evince "%s" &' % pdf)
        return flask.jsonify(result='OK')
    else:
        return error('Only POST allowed', None, 405)

