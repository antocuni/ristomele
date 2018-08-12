from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from server import escpos
db = SQLAlchemy()

class Table(db.Model):
    name = db.Column(db.TEXT, primary_key=True)
    waiter = db.Column(db.TEXT)

    def as_dict(self):
        return dict(
            name=self.name,
            waiter=self.waiter
            )

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DATETIME)
    cashier = db.Column(db.TEXT)
    table = db.Column(db.TEXT)
    waiter = db.Column(db.TEXT)
    customer = db.Column(db.TEXT)
    notes = db.Column(db.TEXT)
    menu = db.Column(db.TEXT)

    @classmethod
    def from_dict(cls, data):
        return cls(
            date = datetime.now(),
            cashier = data['cashier'],
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
            date = self.date.strftime('%Y-%m-%d %H:%M:%S') if self.date else None,
            cashier = self.cashier,
            table = self.table,
            waiter = self.waiter,
            customer = self.customer,
            notes = self.notes,
            menu = self._load_menu())

    def textual_id(self):
        id = ''
        date = ''
        if self.id is not None:
            id = str(self.id)
        if self.date is not None:
            date = self.date.strftime('%d/%m %H:%M')
        return '%s [%s]' % (id, date)

    def drink_receipt(self):
        lines = []
        w = lines.append
        num = self.id or ''
        if self.date:
            date = '[%s]' % self.date.strftime('%d/%m %H:%M')
        else:
            date = ''
        #
        w(escpos.big() + 'Tavolo: %s' % self.table)
        w(escpos.big() + self.waiter)
        w('')
        w(escpos.reset() + 'Numero ordine: %s %s' % (num, date))
        w('Cassiere: %s' % (self.cashier))
        w('Cliente: %s' % self.customer)
        w('')
        menu = json.loads(self.menu)
        for item in menu:
            if item['is_drink'] and item['count'] > 0:
                w('%2d %s' % (item['count'], item['name']))
        w('')
        w('')
        w('')
        w('')
        return '\n'.join(lines)
