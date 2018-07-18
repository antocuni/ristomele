# Same as before, with a kivy-based UI

import time
from jnius import autoclass

BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
UUID = autoclass('java.util.UUID')

PRINTER_NAME = 'BlueTooth Printer'
def print_string(s):
    paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
    socket = None
    print 'bluetooh paired devices:'
    for device in paired_devices:
        print device.getName()
        if device.getName() == PRINTER_NAME:
            print 'Found printer:', PRINTER_NAME
            socket = device.createRfcommSocketToServiceRecord(
                UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
            recv_stream = socket.getInputStream()
            send_stream = socket.getOutputStream()
            break
    print 'Connecting...'
    socket.connect()
    send_stream.write(s)
    send_stream.write('\n\n\n\n')
    send_stream.flush()
    print 'Closing connection'
    time.sleep(0.5)
    socket.close()
