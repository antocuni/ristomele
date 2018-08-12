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

def setup_logging(app):
    logfile = config.ROOT.join('log', 'ristomele.log')
    handler = logging.FileHandler(str(logfile))
    handler.setLevel(logging.INFO)  # only log errors and above
    app.logger.addHandler(handler)  # attach the handler to the app's logger

def create_app(dbpath=DB):
    from server import model
    app = flask.Flask('risto_server', root_path='server')
    setup_logging(app)
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

