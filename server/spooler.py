"""
Usage: spooler SPOOLDIR [options]

Options:

  -p --printer=DEVICE   The device of the printer [Default: /dev/usb/lp0]
  -h --help             Show help
"""

import sys
import time
import traceback
import py
import docopt
import logging
from server import config
LOGFILE = config.ROOT.join('log', 'spooler.log')

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
    printer = py.path.local(args['--printer'])
    #
    logging.info('Spooler starting')
    orders_dir = spooldir.join('orders').ensure(dir=True)
    drinks_dir = spooldir.join('drinks').ensure(dir=True)
    while True:
        logging.info('beat')
        print_orders(orders_dir)
        print_drinks(drinks_dir, printer)
        time.sleep(1)

def print_orders(orders_dir):
    pass

def print_drinks(d, printer):
    try:
        for txt in d.listdir('*.txt'):
            logging.info('Printing %s', txt.basename)
            content = txt.read()
            with printer.open('wb') as f:
                f.write(content)
            txt.remove()
            logging.info('DONE')
    except:
        logging.exception('ERROR!')


if __name__ == '__main__':
    sys.exit(main())
