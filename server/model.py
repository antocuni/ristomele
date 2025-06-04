from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from server import escpos
from server import config
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
        menu = data.get('menu')
        if menu is not None:
            menu = json.dumps(menu)
        return cls(
            date = datetime.now(),
            cashier = data['cashier'],
            table = data['table'],
            waiter = data['waiter'],
            customer = data['customer'],
            notes = data['notes'],
            menu = menu,
            )

    def _load_menu(self):
        try:
            return json.loads(self.menu)
        except ValueError:
            # json decoding error
            return None

    def as_dict(self):
        d = self.as_dict_light()
        d['menu'] = self._load_menu()
        return d

    def as_dict_light(self):
        """
        Like as_dict, but without the menu
        """
        return dict(
            id = self.id,
            date = self.date.strftime('%Y-%m-%d %H:%M:%S') if self.date else None,
            cashier = self.cashier,
            table = self.table,
            waiter = self.waiter,
            customer = self.customer,
            notes = self.notes,
            menu = None)

    def textual_id(self):
        id = ''
        date = ''
        if self.id is not None:
            id = str(self.id)
        if self.date is not None:
            date = self.date.strftime('%d/%m %H:%M')
        return '%s [%s]' % (id, date)

    def drink_receipt(self):
        has_drinks = False
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
                has_drinks = True
        w('')
        w('')
        w('')
        w('')
        w('')
        if has_drinks:
            return '\n'.join(lines)
        else:
            return None

    def is_fila_A(self):
        """
        Only for Sagra: this is a "fila A" order only if it contains only
        drinks and "Zeneize"
        """
        menu = json.loads(self.menu)
        for item in menu:
            is_drink = item['is_drink']
            is_zeneize = 'Zeneize' in item['name']
            if not is_drink and not is_zeneize:
                return False
        return True

    def food_receipt(self, reprint=False):
        if config.MODE == 'sagra' and self.is_fila_A():
            return None # don't print

        def should_include(item):
            if item['count'] <= 0:
                return False
            if item['is_drink'] and config.MODE == 'sagra':
                return False
            return True

        lines = []
        w = lines.append
        num = self.id or ''
        if self.date:
            date = '[%s]' % self.date.strftime('%d/%m %H:%M')
        else:
            date = ''
        #
        if reprint:
            w(escpos.big() + 'RISTAMPA')

        if config.MODE == 'sagra':
            w(escpos.big() + 'Ordine: %s %s' % (num, date))
        else:
            w(escpos.big() + self.waiter)
            w(escpos.reset() + 'Ordine: %s %s' % (num, date))
            w('')
            w(escpos.reset() + 'Tavolo: %s' % self.table)

        w('Cassiere: %s' % (self.cashier))
        w('Cliente: %s' % self.customer)
        w('')
        if self.notes:
            w('Note:')
            w(self.notes)
            w('')
        menu = json.loads(self.menu)
        items_printed = 0
        for item in menu:
            if should_include(item):
                w('%2d %s' % (item['count'], item['name']))
                items_printed += 1
        w('')
        w('')
        w('')
        w('')
        w('')
        w('-------------------------------------')
        w('')
        w('')
        w('')
        w('')
        w('')

        if items_printed > 0:
            return '\n'.join(lines)
        else:
            return None


    def get_total(self):
        menu = self._load_menu()
        total = 0
        for item in menu:
            if item['kind'] != 'item':
                continue
            total += item['count'] * item['price']
        return total
