import random
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from ristomele.gui.uix import FlatButton, MyScreen

class TableButton(FlatButton):
    table = ObjectProperty()

    ## def on_release(self):
    ##     self.table.busy = not self.table.busy


class TableSpinner(Spinner):
    pass


class BaseTablesScreen(MyScreen):
    restaurant = ObjectProperty()

    def __init__(self, **kwds):
        super(BaseTablesScreen, self).__init__(**kwds)
        self.grid = GridLayout(rows=self.restaurant.rows,
                               cols=self.restaurant.cols)
        self.ids.layout.add_widget(self.grid)
        for t in self.restaurant.tables:
            self.grid.add_widget(self.make_widget(t))
        self.update_waiters()

class TablesScreen(BaseTablesScreen):

    def update_waiters(self):
        pass

    def make_widget(self, table):
        return TableButton(table=table)


class MySpinnerOption(FlatButton):
    pass

class EditTablesScreen(BaseTablesScreen):

    def update_waiters(self):
        waiters = ('anto', 'pippo', 'pluto', '...')
        for spinner in self.grid.walk():
            spinner.values = waiters

    def make_widget(self, table):
        def on_text(spinner, text):
            # make sure to show also the table name when we click on a button
            if text.startswith(table.name):
                return
            spinner.text = '%s\n%s' % (table.name, text)
        #
        spinner = Spinner(
            text=table.name,
            values=(),
            option_cls=MySpinnerOption,
        )
        spinner.bind(text=on_text)
        return spinner
