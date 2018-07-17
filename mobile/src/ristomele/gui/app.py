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
import ristomele.gui.uix # side effects
from ristomele.gui import iconfonts
from ristomele.gui.manager import Manager
from ristomele.logger import Logger
from ristomele.gui.tables import Tables
from ristomele.gui.menu import Menu, MenuItem, MenuSeparator

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
        main = Tables(name='main')
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
        items = [MenuItem(name='Coperto'),
                 MenuSeparator(text='Primi'),
                 MenuItem(name='Ravioli'),
                 MenuItem(name='Salsiccia alla piastra')]
        menu = Menu(table=table, items=items)
        self.root.open(menu)

    def submit_menu(self, menu):
        url = self.url('order/')
        payload = dict(
            table=menu.table.text,
            items=[item.as_dict() for item in menu.items],
        )
        requests.post(url, json=payload)


def main():
    iconfonts.init()
    RistoMeleApp().run()

