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
    if spooldir.check(dir=False):
        logging.error('%s is not a valid directory', spooldir)
        return 1
    if printer.check(exists=False):
        logging.error('The printer device %s does not exists', printer)
        return 1
    #
    logging.info('spooler starting')
    while True:
        for txt in spooldir.listdir('*.txt'):
            print_document(txt, printer)
        time.sleep(1)

def print_document(txt, printer):
    try:
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
