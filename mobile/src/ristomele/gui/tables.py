import random
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.app import App
from ristomele.gui.uix import FlatButton, MyScreen, Theme
from ristomele import model

class TableWidget(BoxLayout):
    bgcolor = ObjectProperty()
    table = ObjectProperty(default=model.Table())


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
        app = App.get_running_app()
        def new_order():
            app.new_order(table)

        w = TableWidget(table=table)
        w.ids.main_button.on_release = new_order
        w.ids.name_button.on_release = new_order
        w.ids.main_button.background_color = Theme.BGSUCCESS
        w.ids.main_button.color = Theme.ICON
        w.ids.name_button.background_color = Theme.BGSUCCESS
        return w


class EditTablesScreen(BaseTablesScreen):

    def make_widget(self, table):
        def save_waiter():
            table.waiter = self.ids.waiter_name.text
        def load_waiter():
            self.ids.waiter_name.text = table.waiter

        w = TableWidget(table=table)
        w.ids.main_button.on_release = save_waiter
        w.ids.name_button.on_release = load_waiter
        return w

    def save(self, app):
        app.update_tables(self.restaurant.tables)
        app.root.go_back()

