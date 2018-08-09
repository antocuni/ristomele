from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from ristomele.gui.uix import MyLabel, MyScreen

class OrderItem(BoxLayout):
    order = ObjectProperty()

class OrderListScreen(MyScreen):
    orders = ListProperty()





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
        new_order = app.submit_order(self.order)
        self.order = new_order
        self.ids.content.text = new_order.as_textual_receipt()
        app.print_order(new_order)
        # go back to the table selection screen
        ## app.root.go_back()
        ## app.root.go_back()

    def update_rest(self):
        try:
            got = float(self.ids.money.text)
        except ValueError:
            rest = 0
        else:
            rest = got - self.order.get_total()
        self.ids.rest.text = 'Resto: %.2f' % rest
