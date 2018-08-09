from datetime import datetime
from kivy.event import EventDispatcher
from kivy.properties import (StringProperty, ObjectProperty, ListProperty,
                             BooleanProperty, NumericProperty, OptionProperty)

class Table(EventDispatcher):
    name = StringProperty()
    waiter = StringProperty()
    busy = BooleanProperty(False)

    def as_dict(self):
        return dict(name=self.name, waiter=self.waiter)

class Restaurant(EventDispatcher):
    tables = ListProperty()

    def __init__(self, rows=5, cols=3):
        self.rows = rows
        self.cols = cols
        tables = []
        for row in range(self.rows):
            for col in range(self.cols):
                tname = '%s%s' % (col+1, row+1)
                tables.append(Table(name=tname))
        super(Restaurant, self).__init__(tables=tables)


class MenuItem(EventDispatcher):
    kind = OptionProperty("item", options=["item", "separator"])
    name = StringProperty()
    count = NumericProperty(default=0)
    price = NumericProperty(default=0)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def as_dict(self):
        return dict(kind=self.kind,
                    name=self.name,
                    count=self.count,
                    price=self.price)


class Order(EventDispatcher):
    id = ObjectProperty()
    date = ObjectProperty()
    table = ObjectProperty()
    customer = StringProperty()
    notes = StringProperty()
    menu = ListProperty() # list of MenuItem

    @classmethod
    def from_dict(cls, data):
        date = data.get('date')
        if date is not None:
            date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        table = Table(name=data['table'], waiter=data['waiter'])
        return cls(
            id = data.get('id'),
            date = date,
            table = table,
            customer = data['customer'],
            notes = data['notes'],
            menu = [MenuItem.from_dict(d) for d in data['menu']]
            )

    def as_dict(self):
        return dict(
            table=self.table.name,
            waiter=self.table.waiter,
            customer=self.customer,
            notes=self.notes,
            menu=[item.as_dict() for item in self.menu],
        )

    def as_textual_receipt(self, width=32):
        lines = []
        w = lines.append
        num = self.id or ''
        if self.date:
            date = '[%s]' % self.date.strftime('%d/%m %H:%M')
        else:
            date = ''
        w('Numero ordine: %s %s' % (num, date))
        w('Tavolo: %s' % self.table.name)
        w('Cliente: %s' % self.customer)
        w('')
        total = 0
        for item in self.menu:
            if item.kind != 'item':
                continue
            if item.count == 0:
                continue
            subtot = item.count * item.price
            descr = item.name
            price = '%s %5.2f' % (('x%d' % item.count).ljust(3), subtot)
            total += subtot
            #
            descr = (descr + ' ')[:width]
            if len(descr) + len(price) > width:
                # print on two separate lines
                w(descr)
                w(price.rjust(width))
            else:
                # print on a single line
                line = '%s%s' % (descr, price.rjust(width-len(descr)))
                w(line)
        w('')
        line = 'TOTALE: %.2f' % total
        w(line.rjust(width))
        w('')
        w('RICEVUTA NON FISCALE')
        return '\n'.join(lines)
