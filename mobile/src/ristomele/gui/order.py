from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from ristomele.gui.uix import MyLabel, MyScreen

class MenuItem(BoxLayout):
    item = ObjectProperty()

class MenuSeparator(BoxLayout):
    item = ObjectProperty()


class NewOrderScreen(MyScreen):
    order = ObjectProperty()

    def item_class(self, x, index):
        if x.kind == 'item':
            return MenuItem(item=x)
        else:
            return MenuSeparator(item=x)

    def submit(self, app):
        self.order.customer = self.ids.customer_name.text
        self.order.notes = self.ids.notes.text
        app.show_order(self.order)


class ShowOrderScreen(MyScreen):
    order = ObjectProperty()

    def submit(self, app):
        app.submit_order(self.order)