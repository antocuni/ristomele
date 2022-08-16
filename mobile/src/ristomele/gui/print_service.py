import time
import Queue
import threading
from contextlib import contextmanager
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.properties import (StringProperty, ObjectProperty)
from kivy.clock import Clock, mainthread
from ristomele.logger import Logger
from ristomele.gui.error import ErrorMessage

class PrintService(EventDispatcher):
    app = ObjectProperty()
    status = StringProperty("ok") # ok, printing, error
    status_class = StringProperty("primary")

    # ==============================
    # Main thread
    # ==============================

    def __init__(self, **kwargs):
        super(PrintService, self).__init__(**kwargs)
        self.thread = threading.Thread(target=self.run, name='PrintService')
        self.thread.daemon = True
        self.to_print = Queue.Queue()
        self.running = False

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        # give the sync thread enough time to shut down gracefully. If it
        # takes more than 1 seconds, the whole thread will be brutally killed
        # because daemon==True
        self.running = False
        # put something to ensure that the queue is not empty
        self.to_print.put((None, None))
        self.thread.join(1)

    @mainthread
    def set_status(self, status, cssclass):
        self.status = status
        self.status_class = cssclass

    @contextmanager
    def printing(self):
        self.set_status('printing', 'warning')
        try:
            yield
        except Exception, e:
            self.set_status('error', 'danger')
            self.app.exception_handler.handle_exception(e)
        else:
            self.set_status('ok', 'primary')

    def submit(self, printer_name, text):
        self.to_print.put((printer_name, text))

    # ==============================
    # PrintService thread
    # ==============================

    def run(self):
        Logger.info('PrintService: thread started')
        while self.running:
            printer_name, text = self.to_print.get() # blocking
            if text is None:
                # probably put by .stop()
                Logger.info('PrintService: text is None, ignoring')
                continue
            Logger.info('PrintService: got text, printing: %s' % text[:50])
            with self.printing():
                if platform == 'android':
                    from ristomele.gui.printer import print_string
                    print_string(printer_name, text)
                elif platform == 'linux':
                    from ristomele.gui.linux_printer import print_string
                    print_string(text)
                else:
                    print 'Fake connection to the printer...'
                    time.sleep(2)
                    print
                    print text
                    print
        Logger.info('PrintService: stop')
