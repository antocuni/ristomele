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

    @property
    def customer(self):
        return self.ids.customer_name.text

    def as_textual_receipt(self):
        WIDTH = 32
        lines = []
        w = lines.append
        w('RICEVUTA')
        w('Numero ordine: xxx')
        w('Tavolo: %s' % self.table.text)
        w('Cliente: %s' % self.customer)
        w('')
        total = 0
        for item in self.items:
            if not isinstance(item, MenuItem):
                continue
            if item.count == 0:
                continue
            subtot = item.count * item.price
            descr = item.name
            price = '%s %5.2f' % (('x%d' % item.count).ljust(3), subtot)
            total += subtot
            #
            descr = (descr + ' ')[:WIDTH]
            if len(descr) + len(price) > WIDTH:
                # print on two separate lines
                w(descr)
                w(price.rjust(WIDTH))
            else:
                # print on a single line
                line = '%s%s' % (descr, price.rjust(WIDTH-len(descr)))
                w(line)
        w('')
        line = 'TOTALE: %.2f' % total
        w(line.rjust(WIDTH))
        return '\n'.join(lines)
