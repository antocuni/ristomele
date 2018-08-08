from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DATETIME)
    table = db.Column(db.TEXT)
    waiter = db.Column(db.TEXT)
    customer = db.Column(db.TEXT)
    notes = db.Column(db.TEXT)
    menu = db.Column(db.TEXT)

    @classmethod
    def from_dict(cls, data):
        return cls(
            date = datetime.now(),
            table = data['table'],
            waiter = data['waiter'],
            customer = data['customer'],
            notes = data['notes'],
            menu = json.dumps(data['menu'])
            )

    def _load_menu(self):
        try:
            return json.loads(self.menu)
        except ValueError:
            # json decoding error
            return None

    def as_dict(self):
        return dict(
            id = self.id,
            date = self.date.isoformat() if self.date else None,
            table = self.table,
            waiter = self.waiter,
            customer = self.customer,
            notes = self.notes,
            menu = self._load_menu())

    def textual_id(self):
        date = ''
        if self.date is not None:
            date = self.date.strftime('%d/%m %H:%M')
        return '%d [%s]' % (self.id, date)
