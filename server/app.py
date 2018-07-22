import os
import py
import json
import flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename
from server import config
from server import srczip
from server import ristomele

app = flask.Flask('risto_server', root_path='server')
MOBILE = config.ROOT.join('mobile')
DB = config.ROOT.join('db.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % DB

db = SQLAlchemy(app)
from server import model
db.create_all()

srczip.add_routes(app)
ristomele.add_routes(app)
