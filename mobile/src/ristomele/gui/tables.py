import random
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from ristomele.gui.uix import FlatButton, MyScreen

class TableButton(FlatButton):
    table = ObjectProperty()

    ## def on_release(self):
    ##     self.table.busy = not self.table.busy


class TablesScreen(MyScreen):
    restaurant = ObjectProperty()

    def __init__(self, **kwds):
        super(TablesScreen, self).__init__(**kwds)
        self.grid = GridLayout(rows=self.restaurant.rows,
                               cols=self.restaurant.cols)
        self.ids.layout.add_widget(self.grid)
        for t in self.restaurant.tables:
            self.grid.add_widget(TableButton(table=t))
