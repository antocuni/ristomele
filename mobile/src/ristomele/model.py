from kivy.event import EventDispatcher
from kivy.properties import (StringProperty, ObjectProperty, ListProperty,
                             BooleanProperty)

class Table(EventDispatcher):
    name = StringProperty()
    waiter = StringProperty()
    busy = BooleanProperty(False)


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
