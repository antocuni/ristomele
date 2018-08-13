import os
import py
import json
import flask
import logging
from server import config
from server.srczip import srczip
from server.ristomele import ristomele

MOBILE = config.ROOT.join('mobile')
DB = config.ROOT.join('db.sqlite')
SPOOLDIR = py.path.local('/tmp/spooldir').ensure(dir=True)
LOGFILE = config.ROOT.join('log', 'ristomele.log')

def create_app(dbpath=DB):
    from server import model
    app = flask.Flask('risto_server', root_path='server')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % dbpath
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SPOOLDIR'] = SPOOLDIR
    SPOOLDIR.join('orders').ensure(dir=True)
    SPOOLDIR.join('drinks').ensure(dir=True)
    app.register_blueprint(srczip)
    app.register_blueprint(ristomele)
    model.db.init_app(app)
    with app.app_context():
        model.db.create_all()
    return app

def create_logged_app():
    from requestlogger import WSGILogger, ApacheFormatter
    handler = logging.FileHandler(str(LOGFILE))
    handler.setLevel(logging.INFO)
    logging.root.addHandler(handler)
    app = create_app()
    logged_app = WSGILogger(app, [handler], ApacheFormatter())
    return logged_app

