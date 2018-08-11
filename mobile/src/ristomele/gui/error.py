from kivy.base import ExceptionHandler, ExceptionManager
from ristomele.gui.uix import MessageBox

class ErrorMessage(Exception):
    """
    This represents a non-fatal exception: the error message will be displayed
    to the user in an error box, and the execution of the app will continue
    """

    def __init__(self, message, description=''):
        self.message = message
        self.description = description


class MyExceptionHandler(ExceptionHandler):

    def __init__(self, add_handler=True):
        if add_handler:
            ExceptionManager.add_handler(self)

    def handle_exception(self, exc):
        if isinstance(exc, ErrorMessage):
            self.show_error(exc.message, exc.description)
            return ExceptionManager.PASS
        return ExceptionManager.RAISE

    def show_error(self, message, description):
        box = MessageBox(title='Errore', message=message, description=description)
        box.open()
