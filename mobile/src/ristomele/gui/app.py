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
from ristomele.menu import get_menu
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

    columns = ConfigParserProperty(1, 'ristomele', 'columns', 'app',
                                   val_type=int)


    # NOTE: we need to use val_type=int, because kivy is buggy with val_type=bool
    is_sagra = ConfigParserProperty(1, 'ristomele', 'is_sagra', 'app',
                                    val_type=int)

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
            'is_sagra': 1,
            'columns': 1,
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
        #box.open()

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

    def new_order_or_show_tables(self):
        # this is a bit magic: it always "unwind" the screenmanager stack to
        # make sure that the tables screen is immediately above the main.
        self.root.unwind('main')

        if self.is_sagra:
            table = model.Table(name="N/A", waiter="N/A")
            self.new_order(table)
        else:
            tables = TablesScreen(name='tables', restaurant=self.load_restaurant())
            self.root.open(tables)

    def edit_tables(self):
        screen = EditTablesScreen(name='edit_tables',
                                  restaurant=self.load_restaurant())
        self.root.open(screen)

    def new_order(self, table):
        items = get_menu()
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

        if self.is_sagra:
            s = order.as_textual_receipt(self)
            s += '\n.\n.\n.' # leave some space for easier cutting
        else:
            s = order.as_textual_receipt(self, title='COPIA CLIENTE')
            s += '\n\n\n%s\n\n\n' % ('-'*32)
            s += order.as_textual_receipt(self, title='COPIA CAMERIERE')

        self.print_service.submit(printer_name, s)

    def bluetooth_info(self):
        from ristomele.gui import printer
        printer.print_all_paired_devices()

def main():
    iconfonts.init()
    RistoMeleApp().run()
