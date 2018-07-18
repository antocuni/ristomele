from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from ristomele.gui.uix import MyLabel, MyScreen

class MenuItem(BoxLayout):
    root = ObjectProperty()
    name = StringProperty()
    count = NumericProperty(default=0)
    price = NumericProperty(default=0)

    def as_dict(self):
        return dict(kind='item', name=self.name, count=self.count)

class MenuSeparator(MyLabel):

    def as_dict(self):
        return dict(kind='separator', name=self.text)


class Menu(MyScreen):
    table = ObjectProperty()
    items = ListProperty()
