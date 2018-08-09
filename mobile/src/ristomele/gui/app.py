# -*- encoding: utf-8 -*-
import os
import pypath
from urlparse import urljoin
import requests
from kivy.app import App
from kivy.resources import resource_find
from kivy.properties import ObjectProperty
from kivy.utils import platform
from kivy.core.window import Window
import ristomele
from ristomele import model
import ristomele.gui.uix # side effects
from ristomele.gui.uix import MyScreen
from ristomele.gui import iconfonts
from ristomele.gui.manager import Manager
from ristomele.logger import Logger
from ristomele.gui.tables import TablesScreen, EditTablesScreen
from ristomele.gui.order import OrderListScreen, NewOrderScreen, ShowOrderScreen

class MainScreen(MyScreen):
    pass

class RistoMeleApp(App):
    from kivy.uix.settings import SettingsWithTabbedPanel as settings_cls

    ROWS = 9
    COLS = 3

    def get_application_config(self):
        root = pypath.local(ristomele.__file__).dirpath().dirpath().dirpath()
        ini = root.join('ristomele.ini')
        Logger.info('config file is %s', ini)
        return str(ini)

    def url(self, path):
        host = self.config.get('server', 'host')
        port = self.config.get('server', 'port')
        base = 'http://%s:%s' % (host, port)
        return urljoin(base, path)

    def build_config(self, config):
        config.setdefaults('server', {
            'host': '192.168.1.3',
            'port': '5000'
        })
        config.setdefaults('ristomele', {
            'cashier': ''
        })

    def get_cashier(self):
        return self.config.get('ristomele', 'cashier')

    def build_settings(self, settings):
        from kivy.config import Config
        settings.add_json_panel('App', self.config,
                                filename=resource_find('data/settings.json'))
        settings.add_json_panel('Scrolling', Config,
                                filename=resource_find('data/scrolling.json'))

    def build(self):
        Window.bind(on_keyboard=self.on_keyboard)
        manager = Manager()
        manager.open(MainScreen())
        return manager

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27: # ESC
            return self.root.go_back()
        return False

    def on_pause(self):
        return True

    def show_orders(self):
        url = self.url('orders/')
        resp = requests.get(url)
        # XXX: check the return state
        order_data = resp.json()
        orders = [model.Order.from_dict(d) for d in order_data]
        screen = OrderListScreen(name='ordini', orders=orders)
        self.root.open(screen)

    def show_tables(self):
        tables = TablesScreen(name='tables', restaurant=self.load_restaurant())
        self.root.open(tables)

    def edit_tables(self):
        screen = EditTablesScreen(name='edit_tables',
                                  restaurant=self.load_restaurant())
        self.root.open(screen)

    def new_order(self, table):
        Item = model.MenuItem
        Sep = lambda name: model.MenuItem(kind='separator', name=name)

        fugassin1 = [
            Sep(name='Focaccini'),
            Item(name='Zeneize de Me', price=1.5),
            Item(name='Stracchino', price=3),
            Item(name='Salame', price=3),
            Item(name='Salame + stracchino', price=4),
            Item(name='Prosciutto cotto', price=3),
            Item(name='Prosciutto cotto + stracchino', price=4.5),
            Item(name='Speck', price=3.5),
            Item(name='Boscaiolo + cotto', price=5),
            Item(name='Boscaiolo + mortadella', price=5),
            Item(name='Boscaiolo + speck', price=5.5),
            Item(name='Wurstel', price=4),
            Item(name='Salsiccia', price=4.5),
            Item(name='Salsiccia + stracchino', price=5.5),

            Item(name='Porchetta', price=5),
            Item(name='Mortadella', price=3),
            Item(name='Mortadella + stracchino', price=4),
            Item(name='Nutella', price=3.5),
        ]

        fugassin2 = [
            Sep(name='Focaccini'),
            Item(name='Zeneize de Me', price=1.5),
            Item(name='Salame', price=3),
            Item(name='Salsiccia', price=4.5),
            Item(name='Nutella', price=3.5),
            Item(name='Prosciutto Cotto', price=3),
            Item(name='Porchetta', price=5),
        ]

        fugassin = fugassin1

        items = [
            Item(name='Coperto', price=1),
            Sep(name='Primi'),
            Item(name='Ravioli', price=7),

            Sep(name='Secondi'),

            Item(name='Salsiccia', price=4),
            Item(name='Salsiccia + patatine', price=5),
            Item(name='Salsiccia + pomodori', price=5),

            Item(name='Porchetta', price=4.5),
            Item(name='Porchetta + patatine', price=5.5),
            Item(name='Porchetta + pomodori', price=5.5),

            Item(name='Arrosto', price=5),
            Item(name='Arrosto + patatine', price=6),
            Item(name='Arrosto + pomodori', price=6),

            Sep(name='Contorni'),

            Item(name='Patatine fritte', price=2),
            Item(name='Pomodori', price=2),

        ] + fugassin + [

            Sep(name='Dolci'),
            Item(name='Dolci misti', price=3),
            Item(name='Semifreddo alla nutella', price=3.5),

            Sep(name='Vino'),
            Item(name='Sangria', price=3.5),
            Item(name='Bottiglia rosso', price=5),
            Item(name='Bottiglia bianco', price=5),

            Item(name='Bicchiere grande rosso ', price=2.5),
            Item(name='Bicchiere grande bianco ', price=2.5),

            Item(name='Bicchiere piccolo rosso ', price=1),
            Item(name='Bicchiere piccolo bianco ', price=1),

            Sep(name='Altre bevande'),

            Item(name='Birra alla spina Weiss', price=4),
            Item(name='Birra alla spina Pils', price=3.5),

            Item(name='Coca Cola', price=1.5),
            Item(name='Fanta', price=1.5),
            Item(name='Gazzosa', price=1.5),
            Item(name='The Limone', price=1.5),
            Item(name='The Pesca', price=1.5),

            Item(name='Acqua naturale 0.5L', price=1),
            Item(name='Acqua frizzante 0.5L', price=1),

            Item(name='Caffe', price=1),
        ]
        order = model.Order(table=table, menu=items,
                            cashier=self.get_cashier())
        screen = NewOrderScreen(name='menu', order=order)
        self.root.open(screen)

    def show_order(self, order):
        screen = ShowOrderScreen(order=order)
        self.root.open(screen)

    def submit_order(self, order):
        url = self.url('orders/')
        payload = order.as_dict()
        resp = requests.post(url, json=payload)
        # XXX: check the return state
        order_data = resp.json()['order']
        new_order = model.Order.from_dict(order_data)
        return new_order

    def update_tables(self, tables):
        url = self.url('tables/')
        payload = [t.as_dict() for t in tables]
        resp = requests.put(url, json=payload)
        # XXX: check the return state

    def load_restaurant(self):
        url = self.url('tables/')
        resp = requests.get(url)
        # XXX: check the return state
        table_data = resp.json()
        return model.Restaurant(self.ROWS, self.COLS, table_data)

    def print_order(self, order):
        s = order.as_textual_receipt()
        if platform == 'android':
            from ristomele.gui.printer import print_string
            print_string(s)
        else:
            print
            print s
            print

def main():
    iconfonts.init()
    RistoMeleApp().run()

