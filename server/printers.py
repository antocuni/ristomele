import glob
import pyudev

context = pyudev.Context()

def red(s):
    RED = '\033[31m'
    RESET = '\033[0m'
    return RED + s + RESET

class LPMatch:

    def __init__(self, vendor=None, model=None, serial=None):
        self.vendor = vendor
        self.model = model
        self.serial = serial

    def __eq__(self, lp):
        if not isinstance(lp, LPrinter):
            return NotImplementedError
        if self.vendor is not None and self.vendor != lp.vendor:
            return False
        if self.model is not None and self.model != lp.model:
            return False
        if self.serial is not None and self.serial != lp.serial:
            return False
        return True

    def find(self, printers):
        for lp in printers:
            if lp == self:
                return lp
        return None

def find_usb_parent(device):
    while device:
        if device.get('ID_SERIAL_SHORT') or device.get('ID_MODEL'):
            return device
        device = device.parent
    return None

class LPrinter:

    def __init__(self, path):
        self.path = path
        self.dev = pyudev.Device.from_device_file(context, path)
        self.parent = find_usb_parent(self.dev)
        self.vendor = self.get('ID_VENDOR')
        self.model = self.get('ID_MODEL')
        self.serial = self.get('ID_SERIAL_SHORT')

    def __repr__(self):
        return "<LPrinter '%s' vendor='%s' model='%s' serial='%s'>" % (
            self.path, self.vendor, self.model, self.serial
        )

    @staticmethod
    def all():
        return [LPrinter(path) for path in glob.glob('/dev/usb/lp*')]

    def get(self, key):
        """
        Get the given key either on the device or on its parent
        """
        if key in self.dev:
            return self.dev[key]
        return self.parent.get(key)

    def pp(self):
        def printdev(path, d):
            HIGHLIGHT = ('ID_MODEL', 'ID_SERIAL_SHORT', 'ID_VENDOR')
            print path
            for key, value in d.items():
                if key in HIGHLIGHT:
                    key = red(key)
                    value = red(value)
                print('    %s: %s' % (key, value))

        printdev(self.path, self.dev)
        if self.parent:
            printdev('<parent>', self.parent)
        else:
            print '<parent>    NOT FOUND'
        print





def main():
    printers = LPrinter.all()
    for lp in printers:
        print lp
        lp.pp()


if __name__ == '__main__':
    main()
