import os
import py
import json
import flask
from server import config
from server.srczip import srczip
from server.ristomele import ristomele

MOBILE = config.ROOT.join('mobile')
DB = config.ROOT.join('db.sqlite')
SPOOLDIR = py.path.local('/tmp/spooldir').ensure(dir=True)

def create_app(dbpath=DB):
    from server import model
    app = flask.Flask('risto_server', root_path='server')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % dbpath
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SPOOLDIR'] = SPOOLDIR
    app.register_blueprint(srczip)
    app.register_blueprint(ristomele)
    model.db.init_app(app)
    with app.app_context():
        model.db.create_all()
    return app

