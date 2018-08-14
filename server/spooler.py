"""
Usage: spooler SPOOLDIR [options]

Options:

  -p --printer=DEVICE   The device of the printer [Default: /dev/usb/lp0]
  --evince              For local development: don't print anything, but
                        show generated pdfs using evince
  -h --help             Show help
"""

import sys
import os
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
    evince = args['--evince']
    spooldir = py.path.local(args['SPOOLDIR'])
    printer = py.path.local(args['--printer'])
    #
    logging.info('Spooler starting')
    orders_dir = spooldir.join('orders').ensure(dir=True)
    drinks_dir = spooldir.join('drinks').ensure(dir=True)
    i = 0
    while True:
        i += 1
        if i % 30 == 0:
            logging.info('I am still alive :)')
        print_orders(orders_dir, evince)
        print_drinks(drinks_dir, printer)
        time.sleep(1)

def exec_cmd(cmdline):
    logging.info('EXEC: %s', cmdline)
    ret = os.system(cmdline)
    if ret != 0:
        logging.error('return value: %s', ret)
        return False
    return True

def print_orders(orders_dir, evince):
    print_cmd = 'lp'
    if evince:
        print_cmd = 'evince'
    try:
        for html in orders_dir.listdir('*.html'):
            logging.info('Found HTML: %s', html.basename)
            pdf = html.new(ext='pdf')
            if not exec_cmd('wkhtmltopdf "%s" "%s"' % (html, pdf)):
                continue
            if not exec_cmd('%s "%s"' % (print_cmd, pdf)):
                continue
            logging.info('Removing %s and %s', html.basename, pdf.basename)
            html.remove()
            pdf.remove()
    except:
        logging.exception('ERROR!')

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
