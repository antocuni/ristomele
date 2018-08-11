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

    def __init__(self, app):
        self.app = app
        ExceptionManager.add_handler(self)

    def handle_exception(self, exc):
        if isinstance(exc, ErrorMessage):
            box = MessageBox(title='Errore', message=exc.message,
                             description=exc.description)
            box.open()
            return ExceptionManager.PASS
        return ExceptionManager.RAISE
