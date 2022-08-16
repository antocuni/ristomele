import pypath
from ristomele import escpos
from ristomele.gui.error import ErrorMessage

def get_printer():
    """
    On linux, we don't select the printer with an option. Instead, we just
    find the first '/dev/usb/lp*' device that we can find.
    """
    lps = pypath.local('/dev/usb').listdir('lp*')
    if len(lps) == 0:
        raise ErrorMessage("Impossibile trovare la stampante.\n"
                           "Controllare che sia accesa e/o provare a\n"
                           "scollegare e ricollegare il cavo")
    lp = lps[0]
    return lp

def print_string(s):
    s = escpos.magic_encode(s)
    s += "\n\n\n\n\n"
    printer = get_printer() # this is a pypath.local
    printer.write(s)
