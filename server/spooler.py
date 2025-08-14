"""
Usage: spooler SPOOLDIR [options]

Options:

  --dev        Development mode
  --show       Show detected printers
  -h --help    Show help
"""

# Printing HTML/PDF/laserjet order: last commit which had the code was 2e72fd2.


import sys
import os
import time
import traceback
import py
import docopt
import logging
import pyudev
import glob

from server import config
LOGFILE = config.ROOT.join('log', 'spooler.log')


# ================ printer detection logic ================

# Printers are selected by PHYSICAL PORT.
# There are some ports which are labeled as "food printers" and others as
# "drink printers".

def get_ristomele_printers(dev):
    """
    Return a dictionary in this form:
        {
            'food': '/dev/usb/lp0',
            'drinks': /dev/usb/lp1'
        }

    If no printer is found for either 'food' or 'drinks', use None.
    """
    if dev:
        return {
            'food': '/dev/tty',
            'drinks': '/dev/tty',
        }

    food_ports = ['1-1', '2-1']
    drinks_ports = ['1-2', '2-2']
    printers = get_all_printers()
    res = {
        'food': None,
        'drinks': None,
    }
    for port in food_ports:
        if port in printers:
            res['food'] = printers[port]['lp']
            break

    for port in drinks_ports:
        if port in printers:
            res['drinks'] = printers[port]['lp']
            break

    return res

def get_description(device):
    """Return a human-readable USB description."""
    vendor = device.get('ID_VENDOR_FROM_DATABASE') or device.get('ID_VENDOR') or ''
    model = device.get('ID_MODEL_FROM_DATABASE') or device.get('ID_MODEL') or ''
    return '{} {}'.format(vendor, model).strip()

def get_all_printers():
    """Return a dict {usb_topo_path: lp_path} for /dev/usb/lp* printers"""
    context = pyudev.Context()
    printers = {}

    for lp_path in glob.glob('/dev/usb/lp*'):
        # Get udev device for this node
        try:
            device = pyudev.Device.from_device_file(context, lp_path)
        except Exception:
            continue  # Skip if we can't get a device

        # Walk up to find the usb_device parent
        parent = device
        while parent and not (parent.subsystem == 'usb' and parent.device_type == 'usb_device'):
            parent = parent.parent

        if parent:
            topo_path = parent.sys_name  # e.g., '1-1'
            if topo_path not in printers:
                printers[topo_path] = {
                    'lp': lp_path,
                    'description': get_description(parent)
                }
    return printers

def show_all_printers():
    print('All printers:')
    printers = get_all_printers()
    for topo_path in sorted(printers.keys()):
        info = printers[topo_path]
        print('  {}: {} {}'.format(topo_path, info['lp'], info['description']))

    print
    print('Ristomele:')
    config = get_ristomele_printers(dev=False)
    for key, value in config.items():
        print('  {}: {}'.format(key, value))

# ============================= main logic ==================================

def setup_logging():
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s',
                                  datefmt='%m/%d/%Y %H:%M:%S')
    logging.root.setLevel(logging.INFO)
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOGFILE))
    ]
    for h in handlers:
        h.setLevel(logging.INFO)
        h.setFormatter(formatter)
        logging.root.addHandler(h)

def main():
    setup_logging()
    args = docopt.docopt(__doc__)
    spooldir = py.path.local(args['SPOOLDIR'])
    dev = args['--dev']
    if '--show' in args:
        show_all_printers()
        return

    #
    logging.info('Spooler starting')
    logging.info('spooldir: %s', spooldir)
    drinks_dir = spooldir.join('drinks').ensure(dir=True)
    food_dir = spooldir.join('food').ensure(dir=True)
    i = 0

    lp_config = None
    while True:
        i += 1
        if i % 600 == 0:
            logging.info('I am still alive :)')
        new_lp_config = get_ristomele_printers(dev)
        if new_lp_config != lp_config:
            logging.info('New LP config detected: %s' % new_lp_config)
            lp_config = new_lp_config

        print_receipt(drinks_dir, lp_config['drinks'])
        print_receipt(food_dir, lp_config['food'])
        time.sleep(1)


def print_receipt(d, printer):
    if printer is None:
        return

    try:
        for txt in d.listdir('*.txt'):
            logging.info('Printing %s/%s', d.basename, txt.basename)
            content = txt.read()
            with open(printer, 'wb') as f:
                f.write(content)
            txt.remove()
            logging.info('DONE')
    except:
        logging.exception('ERROR!')


if __name__ == '__main__':
    sys.exit(main())
