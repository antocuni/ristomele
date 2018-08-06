import json
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    menu = db.Column(db.TEXT)

    def as_dict(self):
        try:
            # menu is already serialized, so we want to dump it as is
            menu = json.loads(self.menu)
        except ValueError:
            # json decoding error
            menu = None
        return dict(id=self.id, menu=menu)

