from kivy.event import EventDispatcher
from kivy.properties import (StringProperty, ObjectProperty, ListProperty,
                             BooleanProperty, NumericProperty, OptionProperty)

class Table(EventDispatcher):
    name = StringProperty()
    waiter = StringProperty()
    busy = BooleanProperty(False)

    def as_dict(self):
        return dict(name=self.name,
                    waiter=self.waiter,
                    busy=self.busy)

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

    def as_dict(self):
        return dict(kind=self.kind,
                    name=self.name,
                    count=self.count,
                    price=self.price)


class Menu(EventDispatcher):
    table = ObjectProperty()
    customer = StringProperty()
    notes = StringProperty()
    items = ListProperty()

    def as_dict(self):
        return dict(
            table=self.table.as_dict(),
            customer=self.customer,
            notes=self.notes,
            menuitems=[item.as_dict() for item in self.items],
        )

