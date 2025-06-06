import time
from jnius import autoclass, JavaException
from ristomele.logger import Logger
from ristomele import escpos
from ristomele.gui.error import ErrorMessage

# this is a hack to make sure that encodings.cp858 is available also on
# android. Needed for escpos.magic_encode
import encodings_cp858


# I couldn't find any official doc for the device class of bluetooth
# printers. Many sources seems to indicate the class is 0x680, however our
# GOOJPRT printer reports as 0x604:
#
#    https://stackoverflow.com/questions/45301406/android-bluetooth-printer-connectivity
#    https://stackoverflow.com/questions/23273355/is-it-possible-to-get-list-of-bluetooth-printers-in-android
#    http://bluetooth-pentest.narod.ru/software/bluetooth_class_of_device-service_generator.html
#
#
BLUETOOTH_PRINTER_CLASS = (0x680, 0x604)

# this is the PDF manual of our printers
# https://www.slideshare.net/AdaiseNascimento/58-mm-mini-portable-thermal-printer-instruction-manual

BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
UUID = autoclass('java.util.UUID')

def get_paired_devices():
    return BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()

def describe_device(device):
    print 'name        :', device.getName()
    print 'major class :', hex(device.getBluetoothClass().getMajorDeviceClass())
    print 'device class:', hex(device.getBluetoothClass().getDeviceClass())
    print 'UUIDs:'
    uuids = device.getUuids()
    if uuids is None:
        print 'None'
    else:
        for uuid in uuids:
            print '   ', uuid.toString()
    print

def print_all_paired_devices():
    print 'Bluetooth paired devices'
    for device in get_paired_devices():
        describe_device(device)

def get_full_name(device):
    """
    Return a string which contains both the name and the bluetooth address
    """
    return '%s\n%s' % (device.getName(), device.getAddress())

def get_all_printers():
    devices = []
    for device in get_paired_devices():
        cls = device.getBluetoothClass().getDeviceClass()
        if cls in BLUETOOTH_PRINTER_CLASS:
            devices.append(device)
    return devices

def get_printer(name):
    printer = None
    for device in get_paired_devices():
        if get_full_name(device) == name:
            printer = device
            break
    #
    if printer is None:
        print 'WARNING: cannot find a printer named', name
        return None
    #
    cls = printer.getBluetoothClass().getDeviceClass()
    if cls not in BLUETOOTH_PRINTER_CLASS:
        print 'WARNING: found device %s, but the class is %s instead of %s' % (
            name, hex(cls), hex(BLUETOOTH_PRINTER_CLASS))
        return None
    #
    print 'Found printer!'
    describe_device(printer)
    return printer

def print_string(printer_name, s):
    s = escpos.magic_encode(s)
    printer = get_printer(printer_name)
    if printer is None:
        raise ErrorMessage(
            message="Impossibile trovare la stampante\n%s" % printer_name,
            description=("Controllare che sia all'interno della lista "
                         '"Dispositivi Associati" nelle opzioni bluetooth '
                         "di Android, poi selezionarla nella schermata "
                         "Opzioni dell'app"))
    #
    try:
        socket = printer.createRfcommSocketToServiceRecord(
            UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
        recv_stream = socket.getInputStream()
        send_stream = socket.getOutputStream()
        print 'Connecting...'
        socket.connect()
        send_stream.write(s)
        send_stream.write('\n\n\n\n\n')
        send_stream.flush()
        print 'Closing connection'
        time.sleep(0.5)
        socket.close()
    except JavaException, e:
        Logger.exception('Error during bluetooth printing')
        raise ErrorMessage(
            message="Impossibile connettersi alla stampante\n%s" % printer_name,
            description=("Controllare che il cellulare abbia il bluetooth "
                         "abilitato e che la stampante sia accesa"))
