from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from ristomele.gui.uix import MyLabel, MyScreen
from ristomele import model

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

    # TEMP: comment out if we don't want to support multiple columns. See also
    # ristomele.kv:NewOrderScreen
    def on_enter(self):
        grid = self.ids.item_grid
        grid.clear_widgets()

        num_columns = grid.cols  # Automatically get number of columns from layout
        col = 0  # Track current column position in the row

        for index, menu_item in enumerate(self.order.menu):
            if menu_item.kind == 'separator':
                # If not at start of row, pad with empty widgets to align separator
                if col != 0:
                    for _ in range(num_columns - col):
                        grid.add_widget(Widget(size_hint_y=None, height=0))
                # Add separator widget (should span full row visually)
                separator = MenuSeparator(item=menu_item)
                separator.size_hint_x = 1
                separator.size_hint_y = None
                if not hasattr(separator, 'height'):
                    separator.height = app.std_height  # fallback
                grid.add_widget(separator)
                # Pad the rest of the row so it aligns
                for _ in range(num_columns - 1):
                    grid.add_widget(Widget(size_hint_y=None, height=0))
                col = 0  # Reset column counter
            else:
                widget = MenuItem(item=menu_item)
                grid.add_widget(widget)
                col += 1
                if col >= num_columns:
                    col = 0

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
    order = ObjectProperty(rebind=True)

    def save_or_reprint(self, app):
        if self.order.is_saved:
            # reprint
            app.reprint_order(self.order)
        else:
            # save
            new_order = app.submit_order(self.order)
            self.order = new_order
            self.ids.content.text = new_order.as_textual_receipt(app)
            app.print_receipt(new_order)

    def go_back_dwim(self, app):
        if self.order.is_saved and app.root.history[-2].name == "new_order":
            # if we come from the "new_order" screen and we have saved the
            # order, what we really want is to go back to the tables
            # screen. Actually, this opens a NEW screen, which is good because
            # it means that the names of waiters are reloaded
            app.show_tables()
        else:
            app.root.go_back()

    def update_rest(self):
        try:
            got = float(self.ids.money.text)
        except ValueError:
            rest = 0
        else:
            rest = got - self.order.get_total()
        self.ids.rest.text = 'Resto: %.2f' % rest
