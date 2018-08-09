import random
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
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
        grid = self.ids.grid
        grid.rows = self.restaurant.rows
        grid.cols = self.restaurant.cols
        for t in self.restaurant.tables:
            grid.add_widget(self.make_widget(t))


class TablesScreen(BaseTablesScreen):

    def make_widget(self, table):
        return TableButton(table=table)



class EditableTable(BoxLayout):
    table = ObjectProperty(default=model.Table())


class EditTablesScreen(BaseTablesScreen):

    def make_widget(self, table):
        def save_waiter():
            table.waiter = self.ids.waiter_name.text
        def load_waiter():
            self.ids.waiter_name.text = table.waiter

        w = EditableTable(table=table)
        w.ids.main_button.on_release = save_waiter
        w.ids.load_button.on_release = load_waiter
        return w

    def save(self, app):
        app.update_tables(self.restaurant.tables)
        app.root.go_back()

