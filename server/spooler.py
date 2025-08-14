"""
Usage: spooler SPOOLDIR [options]

Options:

  --dev        Development mode
  -h --help    Show help
"""

# Printing HTML/PDF/laserjet order: last commit which had the code was 2e72fd2.


# XXX: I don't know what happens if we disconnect/reconnect an LP while the
# spooler is running

import sys
import os
import time
import traceback
import py
import docopt
import logging
from server import config
from server.printers import LPrinter, LPMatch
LOGFILE = config.ROOT.join('log', 'spooler.log')

LP_CONFIG = {}
LP_PREFERENCE = {
    'food': [
        LPMatch(serial="Aclass-8888-12340"),
    ],
    'drinks': [
        LPMatch(vendor="STMicroelectronics", serial="Printer")
    ]
}

def init_LP_CONFIG():
    global LP_CONFIG
    LP_CONFIG = {}
    role_to_printer = find_best_printers(LPrinter.all(), LP_PREFERENCE)
    for role in LP_PREFERENCE:
        lp = role_to_printer.get(role)
        LP_CONFIG[role] = lp.path if lp is not None else None


def find_best_printers(available_printers, role_preferences):
    """
    Returns a dict mapping role name to the best available printer,
    ensuring no printer is assigned to more than one role.
    """
    assigned_printers = set()
    role_to_printer = {}

    for role, preferences in role_preferences.items():
        # Try preferred matches first
        for pref in preferences:
            for printer in available_printers:
                if printer in assigned_printers:
                    continue
                if pref == printer:
                    role_to_printer[role] = printer
                    assigned_printers.add(printer)
                    break
            if role in role_to_printer:
                break

    # Fallback: assign first unassigned printer
    for role in role_preferences:
        if role not in role_to_printer:
            for printer in available_printers:
                if printer not in assigned_printers:
                    role_to_printer[role] = printer
                    assigned_printers.add(printer)
                    break

    return role_to_printer




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
    init_LP_CONFIG()
    args = docopt.docopt(__doc__)
    spooldir = py.path.local(args['SPOOLDIR'])
    keep_pdf = args['--dev']
    if args['--dev']:
        for key in LP_CONFIG:
            LP_CONFIG[key] = '/dev/tty'
    #
    logging.info('Spooler starting')
    logging.info('spooldir: %s', spooldir)
    logging.info('LP_CONFIG: %s', LP_CONFIG)
    drinks_dir = spooldir.join('drinks').ensure(dir=True)
    food_dir = spooldir.join('food').ensure(dir=True)
    i = 0
    while True:
        i += 1
        if i % 600 == 0:
            logging.info('I am still alive :)')
        print_receipt(drinks_dir, LP_CONFIG['drinks'])
        print_receipt(food_dir, LP_CONFIG['food'])
        time.sleep(1)


def print_receipt(d, printer):
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
