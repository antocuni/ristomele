import json
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DATETIME)
    menu = db.Column(db.TEXT)

    def as_dict(self):
        try:
            # menu is already serialized, so we want to dump it as is
            menu = json.loads(self.menu)
        except ValueError:
            # json decoding error
            menu = None
        return dict(id=self.id,
                    date=self.date and self.date.isoformat() or None,
                    menu=menu)

    def textual_id(self):
        date = ''
        if self.date is not None:
            date = self.date.strftime('%d/%m %H:%M')
        return '%d [%s]' % (self.id, date)
