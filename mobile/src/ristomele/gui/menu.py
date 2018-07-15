from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout

class MenuItem(BoxLayout):
    root = ObjectProperty()
    name = StringProperty()
    count = NumericProperty(default=0)

    def as_dict(self):
        return dict(name=self.name, count=self.count)

class Menu(Screen):
    table = ObjectProperty()
    items = ListProperty()
