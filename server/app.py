import os
import py
import json
import flask
from server import config
from server import srczip
from server import ristomele

MOBILE = config.ROOT.join('mobile')
DB = config.ROOT.join('db.sqlite')

def create_app(dbpath=DB):
    from server import model
    app = flask.Flask('risto_server', root_path='server')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % dbpath
    srczip.add_routes(app)
    ristomele.add_routes(app)
    model.db.init_app(app)
    with app.app_context():
        model.db.create_all()
    return app

