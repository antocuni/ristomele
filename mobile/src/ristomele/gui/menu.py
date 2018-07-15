from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout

class MenuItem(BoxLayout):
    root = ObjectProperty()
    name = StringProperty()
    count = NumericProperty(default=0)

class Menu(Screen):
    table = ObjectProperty()
