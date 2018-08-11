from ristomele.gui import error

class FakeMessageBox(object):

    BOXES = []

    def __init__(self, title, message, description):
        self.message = message
        self.description = description

    def open(self):
        self.BOXES.append((self.message, self.description))


def test_MyExceptionHandler(monkeypatch):
    monkeypatch.setattr(error, 'MessageBox', FakeMessageBox)
    handler = error.MyExceptionHandler(add_handler=False)
    ret = handler.handle_exception(ValueError("hello world"))
    assert ret == error.ExceptionManager.RAISE
    #
    exc = error.ErrorMessage("my message", "my description")
    ret = handler.handle_exception(exc)
    assert ret == error.ExceptionManager.PASS
    assert FakeMessageBox.BOXES == [
        ("my message", "my description")
        ]
