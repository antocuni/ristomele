from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout

class Tables(Screen):

    ROWS = 7
    COLS = 3

    def __init__(self, **kwds):
        super(Tables, self).__init__(**kwds)
        self.grid = GridLayout(rows=self.ROWS, cols=self.COLS)
        self.ids.layout.add_widget(self.grid)
        for row in range(self.ROWS):
            for col in range(self.COLS):
                tname = '%s%s' % (row+1, col+1)
                self.grid.add_widget(Button(text=tname))
