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
from ristomele.gui import iconfonts
from ristomele.gui.manager import Manager
from ristomele.logger import Logger
from ristomele.gui.tables import TablesScreen
from ristomele.gui.menu import MenuScreen

class RistoMeleApp(App):
    from kivy.uix.settings import SettingsWithTabbedPanel as settings_cls
    sync = ObjectProperty()

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

    def build_settings(self, settings):
        from kivy.config import Config
        settings.add_json_panel('App', self.config,
                                filename=resource_find('data/settings.json'))
        settings.add_json_panel('Scrolling', Config,
                                filename=resource_find('data/scrolling.json'))

    def build(self):
        Window.bind(on_keyboard=self.on_keyboard)
        manager = Manager()
        restaurant = model.Restaurant()
        main = TablesScreen(name='main', restaurant=restaurant)
        manager.open(main)
        return manager

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27: # ESC
            return self.root.go_back()
        return False

    def on_pause(self):
        return True

    ## def on_stop(self):
    ##     self.sync.stop()

    def new_order(self, table):
        Item = model.MenuItem
        Sep = lambda name: model.MenuItem(kind='separator', name=name)
        items = [Item(name='Coperto', price=1),
                 Sep(name='Primi'),
                 Item(name='Ravioli', price=7),
                 Sep(name='Secondi'),
                 Item(name='Salsiccia alla piastra', price=4),
                 Item(name='Salsiccia alla piastra + contorno', price=5),
                 Item(name='Arrosto di manzo', price=5),
                 Item(name='Arrosto di manzo + contorno', price=6),
                 Sep(name='Contorni'),
                 Item(name='Patatine fritte', price=2),
                 Item(name='Pomodori', price=2),
                 Sep(name='Dolci'),
                 Item(name='Dolci misti', price=3),
                 Item(name='Semifreddo alla nutella', price=3.5),
                 Sep(name='Bevande'),
                 Item(name='Bottiglia vino rosso', price=5),
                 Item(name='Bottiglia vino bianco', price=5),
                 Item(name='Birra alla spina', price=3.5),
                 Item(name='Lattine - Bottiglietta The', price=1.5),
                 Item(name='Acqua minerale piccola', price=1),
                 Item(name='Caffe', price=1),
                 ]
        menu = model.Menu(table=table, items=items)
        screen = MenuScreen(name='menu', menu=menu)
        self.root.open(screen)

    def submit_menu(self, menu):
        url = self.url('orders/')
        payload = menu.as_dict()
        requests.post(url, json=payload)
        # XXX check the response
        self.print_menu(menu)

    def print_menu(self, menu):
        s = menu.as_textual_receipt()
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

