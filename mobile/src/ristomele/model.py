#-*- encoding: utf-8 -*-

from ristomele import escpos
from datetime import datetime
from kivy.event import EventDispatcher
from kivy.properties import (StringProperty, ObjectProperty, ListProperty,
                             BooleanProperty, NumericProperty, OptionProperty,
                             AliasProperty)

class Table(EventDispatcher):
    name = StringProperty()
    waiter = StringProperty()
    busy = BooleanProperty(False)

    def as_dict(self):
        return dict(name=self.name, waiter=self.waiter)

class Restaurant(EventDispatcher):
    tables = ListProperty()

    def __init__(self, rows=5, cols=3, table_data=()):
        name2waiter = {}
        for d in table_data:
            name2waiter[d['name']] = d['waiter']
        #
        self.rows = rows
        self.cols = cols
        tables = []
        for row in range(self.rows):
            for col in range(self.cols):
                i = (col*self.rows) + row + 1
                tname = str(i)
                waiter = name2waiter.get(tname, '')
                tables.append(Table(name=tname, waiter=waiter))
        super(Restaurant, self).__init__(tables=tables)


class MenuItem(EventDispatcher):
    kind = OptionProperty("item", options=["item", "separator"])
    name = StringProperty()
    count = NumericProperty(0)
    price = NumericProperty(0)
    is_drink = BooleanProperty(False)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def as_dict(self):
        return dict(kind=self.kind,
                    name=self.name,
                    count=self.count,
                    price=self.price,
                    is_drink=self.is_drink)


class Order(EventDispatcher):
    id = ObjectProperty()
    date = ObjectProperty()
    cashier = StringProperty()
    table = ObjectProperty()
    customer = StringProperty()
    notes = StringProperty()
    menu = ListProperty() # list of MenuItem

    def is_saved(self):
        return self.id is not None
    is_saved = AliasProperty(is_saved, bind=['id'])

    @classmethod
    def from_dict(cls, data):
        date = data.get('date')
        if date is not None:
            date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        table = Table(name=data['table'], waiter=data['waiter'])
        #
        if data.get('menu') is None:
            # XXX: we should somehow mark the Order as "light" or "incomplete"
            menu = []
        else:
            menu = [MenuItem.from_dict(d) for d in data['menu']]
        #
        return cls(
            id = data.get('id'),
            date = date,
            cashier = data['cashier'],
            table = table,
            customer = data['customer'],
            notes = data['notes'],
            menu = menu
            )

    def textual_id(self):
        id = ''
        date = ''
        if self.id is not None:
            id = str(self.id)
        if self.date is not None:
            date = self.date.strftime('%d/%m %H:%M')
        return '%s [%s]' % (id, date)

    def as_dict(self):
        return dict(
            cashier=self.cashier,
            table=self.table.name,
            waiter=self.table.waiter,
            customer=self.customer,
            notes=self.notes,
            menu=[item.as_dict() for item in self.menu],
        )

    def get_total(self):
        total = 0
        for item in self.menu:
            if item.kind != 'item':
                continue
            total += item.count * item.price
        return total

    def is_fila_A(self):
        """
        THIS LOGIC MUST BE MANUALLY KEPT IN SYNC WITH
        server/model.py:is_fila_A()

        Only for Sagra: this is a "fila A" order only if it contains only
        drinks and "Zeneize"
        """
        for item in self.menu:
            is_drink = item.is_drink
            is_zeneize = 'Zeneize' in item.name
            if item.count > 0 and not is_drink and not is_zeneize:
                return False
        return True

    def _receipt_info(self, app, w, use_escpos):
        num = self.id or ''
        if self.date:
            date = u'[%s]' % self.date.strftime('%d/%m %H:%M')
        else:
            date = u''

        if app.is_sagra:
            fila = u'Fila A' if self.is_fila_A() else u'Fila B'
            if use_escpos:
                w(escpos.big() + fila)
                w(escpos.reset())
            else:
                w(fila)
            w(u'Numero ordine: %s %s' % (num, date))
            w(u'Cassiere: %s' % (self.cashier))
            w(u'Cliente: %s' % self.customer)
        else:
            w(u'Numero ordine: %s %s' % (num, date))
            w(u'Tavolo: %s [%s]' % (self.table.name, self.table.waiter))
            w(u'Cassiere: %s' % (self.cashier))
            w(u'Cliente: %s' % self.customer)

    def as_textual_receipt(self, app, width=32, title=u'', use_escpos=True):
        lines = []
        w = lines.append
        w(title)
        self._receipt_info(app, w, use_escpos)
        w('')
        for item in self.menu:
            if item.kind != 'item':
                continue
            if item.count == 0:
                continue
            subtot = item.count * item.price
            descr = item.name
            price = u'%s %5.2f €' % (('x%d' % item.count).ljust(3), subtot)
            #
            descr = (descr + ' ')[:width]
            if len(descr) + len(price) > width:
                # print on two separate lines
                w(descr)
                w(price.rjust(width))
            else:
                # print on a single line
                line = u'%s%s' % (descr, price.rjust(width-len(descr)))
                w(line)
        w(u'')
        line = u'TOTALE: %.2f €' % self.get_total()
        w(line.rjust(width))
        w(u'')
        w(u'RICEVUTA NON FISCALE')
        return u'\n'.join(lines)
