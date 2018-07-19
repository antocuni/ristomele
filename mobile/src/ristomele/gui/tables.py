import random
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.properties import BooleanProperty
from ristomele.gui.uix import FlatButton, MyScreen

class Table(FlatButton):
    busy = BooleanProperty()

    ## def on_release(self):
    ##     self.busy = not self.busy


class Tables(MyScreen):

    ROWS = 5
    COLS = 3

    def __init__(self, **kwds):
        super(Tables, self).__init__(**kwds)
        self.grid = GridLayout(rows=self.ROWS, cols=self.COLS)
        self.ids.layout.add_widget(self.grid)
        for row in range(self.ROWS):
            for col in range(self.COLS):
                tname = '%s%s' % (col+1, row+1)
                self.grid.add_widget(Table(text=tname,
                                           busy=False,
                                           #busy=random.choice([0, 0, 0, 1]),
                                           ))
