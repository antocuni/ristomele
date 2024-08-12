# -*- encoding: utf-8 -*-
import os
import time
import pypath
from urlparse import urljoin
from datetime import datetime
from kivy.app import App
from kivy.resources import resource_find
from kivy.properties import ObjectProperty, ConfigParserProperty, AliasProperty
from kivy.metrics import dp
from kivy.core.window import Window
import ristomele
from ristomele import model
import ristomele.gui.uix # side effects
from ristomele.gui.uix import MyScreen, MessageBox
from ristomele.gui import iconfonts
from ristomele.gui.manager import Manager
from ristomele.logger import Logger
from ristomele.gui.print_service import PrintService
from ristomele.gui.util import SmartRequests, make_bluetooth_printer_setting
from ristomele.gui.error import MyExceptionHandler, ErrorMessage
from ristomele.gui.tables import TablesScreen, EditTablesScreen
from ristomele.gui.order import OrderListScreen, NewOrderScreen, ShowOrderScreen

class MainScreen(MyScreen):
    pass

class RistoMeleApp(App):
    from kivy.uix.settings import SettingsWithTabbedPanel as settings_cls

    ROWS = 9
    COLS = 3

    # these are needed so that we can change to font size in the options
    font_size = ConfigParserProperty(15.0, 'ristomele', 'font_size', 'app',
                                     val_type=float)
    std_height = AliasProperty(lambda self: self.font_size * 2,
                               bind=['font_size'])


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
            'host': '192.168.1.6',
            'port': '5000',
            'timeout': '3',
        })
        config.setdefaults('ristomele', {
            'cashier': '',
            'printer': '',
            'print_waiter_copy': True,
        })

    def get_cashier(self):
        return self.config.get('ristomele', 'cashier')

    def get_timeout(self):
        timeout = self.config.get('server', 'timeout')
        try:
            return float(timeout)
        except ValueError:
            return 3 # this should never happen, but whatever

    def get_printer_name(self):
        return self.config.get('ristomele', 'printer')

    def build_settings(self, settings):
        from kivy.config import Config
        settings.register_type("bluetooth_printer",
                               make_bluetooth_printer_setting)
        settings.add_json_panel('App', self.config,
                                filename=resource_find('data/settings.json'))
        settings.add_json_panel('Scrolling', Config,
                                filename=resource_find('data/scrolling.json'))

    def build(self):
        #self.bluetooth_info()
        self.print_service = PrintService(app=self)
        self.print_service.start()
        self.exception_handler = MyExceptionHandler()
        self.requests = SmartRequests(self)
        Window.bind(on_keyboard=self.on_keyboard)
        manager = Manager()
        manager.open(MainScreen(name='main'))
        return manager

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27: # ESC
            return self.root.go_back()
        return False

    def on_start(self):
        box = MessageBox(title='Avviso',
                         message="Ricordarsi di impostare l'ora sul server")
        box.open()

    def on_pause(self):
        return True

    def on_stop(self):
        self.print_service.stop()
        pass

    def show_orders(self):
        url = self.url('orders/')
        resp = self.requests.get(url,
                            error="Impossibile caricare l'elenco degli ordini")
        order_data = resp.json()
        orders = [model.Order.from_dict(d) for d in order_data]
        screen = OrderListScreen(name='list_orders', orders=orders)
        self.root.open(screen)

    def show_tables(self):
        # this is a bit magic: it always "unwind" the screenmanager stack to
        # make sure that the tables screen is immediately above the main.
        self.root.unwind('main')
        tables = TablesScreen(name='tables', restaurant=self.load_restaurant())
        self.root.open(tables)

    def edit_tables(self):
        screen = EditTablesScreen(name='edit_tables',
                                  restaurant=self.load_restaurant())
        self.root.open(screen)

    def new_order(self, table):
        Item = model.MenuItem
        Drink = lambda name, price: model.MenuItem(name=name, price=price, is_drink=True)
        Foc = lambda name, price: model.MenuItem(name='Foc. '+ name, price=price)
        Sep = lambda name: model.MenuItem(kind='separator', name=name)

        # ====== 13 agosto, fugassin =====

        items_13 = [
            Sep(name='Focaccini'),
            Foc(name='Zeneize de Me', price=2),
            Foc(name='Boscaiolo + cotto', price=5.5),
            Foc(name='Cotto', price=4),
            Foc(name='Cotto + pistacchio', price=5),
            Foc(name='Cotto + stracchino', price=5),
            Foc(name='Cotto + stracch + pist', price=6),
            Foc(name='Porchetta', price=5),
            Foc(name='Porchetta + pistacchio', price=6),
            Foc(name='Salame', price=4),
            Foc(name='Salsiccia', price=5),
            Foc(name='Stracchino', price=4),
            Foc(name='Stracchino + pistacchio', price=5),
            Foc(name='Nutella', price=4),

            Sep(name='Alla piastra'),
            Item(name='Salsiccia', price=4),
            Item(name='Salsiccia + patatine', price=5),
            Item(name='Porchetta', price=4),
            Item(name='Porchetta + patatine', price=5),
            Item(name='Patatine fritte', price=2.5),

            Sep(name='Vino'),
            Drink(name='Bicchiere piccolo rosso ', price=1.5),
            Drink(name='Bicchiere piccolo bianco ', price=1.5),
            Drink(name='Bicchiere grande rosso ', price=3),
            Drink(name='Bicchiere grande bianco ', price=3),
            Drink(name='Sangria', price=4),

            Sep(name='Altre bevande'),
            Drink(name='Birra alla spina PILS', price=5),
            Drink(name='Coca Cola', price=2),
            Drink(name='Aranciata', price=2),
            Drink(name='Gazzosa', price=2),
            Drink(name='The Limone', price=2),
            Drink(name='The Pesca', price=2),

            Drink(name='Acqua naturale 0.5L', price=1),
            Drink(name='Acqua frizzante 0.5L', price=1),
            Drink(name='Bicchiere Spuma', price=0.5),
            Drink(name='Bottiglia Spuma', price=3),
            Item(name='Caffe', price=1),
        ]

        # ====== 14/15 agosto, ristorante =====

        items_14 = [
            Item(name='Coperto', price=1.5),
            Sep(name='Primi'),
            Item(name='Ravioli au Tuccu', price=8),
            Item(name='Trenette al pesto', price=6.5),

            Sep(name='Secondi'),
            Item(name='Salsiccia', price=4),
            Item(name='Salsiccia + patatine', price=5),
            Item(name='Salsiccia + pomodori', price=5),
            Item(name='Salsiccia + verdure', price=5),

            Item(name='Porchetta', price=4),
            Item(name='Porchetta + patatine', price=5),
            Item(name='Porchetta + pomodori', price=5),
            Item(name='Porchetta + verdure', price=5),

            Item(name='Arrosto', price=5),
            Item(name='Arrosto + patatine', price=6),
            Item(name='Arrosto + pomodori', price=6),
            Item(name='Arrosto + verdure', price=6),

            Sep(name='Contorni'),
            Item(name='Patatine fritte', price=2.5),
            Item(name='Pomodori', price=2),
            Item(name='Verdure grigliate', price=2.5),

            Sep(name='Dolci'),
            Item(name='Panna cotta caramello', price=3),
            Item(name='Panna cotta cioccolato', price=3),
            Item(name='Panna cotta frutti di bosco', price=3),
            Item(name='Torte miste', price=3),

            Sep(name='Vino'),
            Drink(name='Sangria', price=4),
            Drink(name='Bottiglia Barbera ', price=8),
            Drink(name='Bottiglia Bonarda ', price=8),
            Drink(name='Bottiglia bianco ', price=8),
            Drink(name='Bicchiere piccolo Barbera ', price=1.5),
            Drink(name='Bicchiere piccolo Bonarda ', price=1.5),
            Drink(name='Bicchiere piccolo bianco ', price=1.5),
            Drink(name='Bicchiere grande Barbera ', price=3),
            Drink(name='Bicchiere grande Bonarda ', price=3),
            Drink(name='Bicchiere grande bianco ', price=3),

            Sep(name='Altre bevande'),
            Drink(name='Birra alla spina PILS', price=5),
            Drink(name='Birra alla spina WEISS', price=5),
            Drink(name='Bicchiere Spuma', price=0.5),
            Drink(name='Coca Cola', price=2),
            Drink(name='Aranciata', price=2),
            Drink(name='Gazzosa', price=2),
            Drink(name='The Limone', price=2),
            Drink(name='The Pesca', price=2),
            Drink(name='Acqua naturale 0.5L', price=1),
            Drink(name='Acqua frizzante 0.5L', price=1),
            Item(name='Caffe', price=1),
        ]

        items = items_14
        order = model.Order(table=table, menu=items,
                            cashier=self.get_cashier())
        screen = NewOrderScreen(name='new_order', order=order)
        self.root.open(screen)

    def show_order(self, order, reload=False):
        if reload:
            url = self.url('orders/%s/' % order.id)
            resp = self.requests.get(url, error="Impossibile caricare l'ordine")
            order_data = resp.json()['order']
            order = model.Order.from_dict(order_data)
        screen = ShowOrderScreen(title='order', order=order)
        self.root.open(screen)

    def submit_order(self, order):
        url = self.url('orders/')
        payload = order.as_dict()
        error = ("ATTENZIONE!\n"
                 "Impossibile contattare il server\n"
                 "L'ordine NON È STATO INVIATO")
        resp = self.requests.post(url, json=payload, error=error)
        order_data = resp.json()['order']
        new_order = model.Order.from_dict(order_data)
        return new_order

    def reprint_order(self, order):
        if order.id is None:
            raise ErrorMessage("Impossibile stampare un ordine se non è stato prima salvato")
        url = self.url('orders/%s/print/' % order.id)
        resp = self.requests.post(url)
        assert resp.status_code == 200

    def print_drinks(self, order):
        if order.id is None:
            raise ErrorMessage("Impossibile stampare un ordine se non è stato prima salvato")
        url = self.url('orders/%s/print_drinks/' % order.id)
        resp = self.requests.post(url)
        assert resp.status_code == 200

    def update_tables(self, tables):
        url = self.url('tables/')
        payload = [t.as_dict() for t in tables]
        resp = self.requests.put(url, json=payload,
                            error="Impossibile salvare le modifiche ai tavoli")
        assert resp.status_code == 200

    def load_restaurant(self):
        url = self.url('tables/')
        resp = self.requests.get(url,
                                 error="Impossibile caricare l'elenco dei tavoli")
        table_data = resp.json()
        return model.Restaurant(self.ROWS, self.COLS, table_data)

    def set_timestamp(self):
        url = self.url('timestamp/')
        payload = {'timestamp': time.time()}
        resp = self.requests.post(url, json=payload,
                                 error="Impossibile impostare l'ora sul server")
        assert resp.status_code == 200
        server_timestamp = resp.json()['timestamp']
        dt = datetime.fromtimestamp(server_timestamp)
        formatted = dt.strftime('%d/%m/%Y %H:%M:%S')
        box = MessageBox(title='Operazione completata',
                         message='Ora sul server impostata a:\n %s' % formatted)
        box.open()

    def print_receipt(self, order):
        printer_name = self.get_printer_name()
        if not printer_name:
            raise ErrorMessage(
                message="Nessuna stampante configurata",
                description="Selezionarne una nella schermata opzioni")
        s = order.as_textual_receipt()

        ## opt = self.config.get('ristomele', 'print_waiter_copy')
        ## if opt and opt != '0':
        if True:
            s += '\n\n\n%s\n\n\n' % ('-'*32)
            s += order.as_textual_receipt(title='COPIA CAMERIERE')
        self.print_service.submit(printer_name, s)

    def bluetooth_info(self):
        from ristomele.gui import printer
        printer.print_all_paired_devices()

def main():
    iconfonts.init()
    RistoMeleApp().run()
