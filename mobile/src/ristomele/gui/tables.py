import random
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from ristomele.gui.uix import FlatButton, MyScreen
from ristomele import model


class TableButton(FlatButton):
    table = ObjectProperty()

    ## def on_release(self):
    ##     self.table.busy = not self.table.busy


class BaseTablesScreen(MyScreen):
    restaurant = ObjectProperty()

    def __init__(self, **kwds):
        super(BaseTablesScreen, self).__init__(**kwds)
        self.grid = GridLayout(rows=self.restaurant.rows,
                               cols=self.restaurant.cols)
        self.ids.layout.add_widget(self.grid)
        for t in self.restaurant.tables:
            self.grid.add_widget(self.make_widget(t))


class TablesScreen(BaseTablesScreen):

    def make_widget(self, table):
        return TableButton(table=table)



class EditableTable(FlatButton):
    table = ObjectProperty(default=model.Table())


class EditTablesScreen(BaseTablesScreen):

    def make_widget(self, table):
        w = EditableTable(table=table,
                          on_release=self.update_waiter)
        return w

    def update_waiter(self, editable_table):
        editable_table.table.waiter = self.ids.waiter_name.text
