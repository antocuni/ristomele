"""
Usage: spooler SPOOLDIR [options]

Options:

  --dev        Development mode
  -h --help    Show help
"""

# NOTE: by default we print to /dev/usb/lp-thermal: this is a symlink which is
# created by a custom udev rule: look at etc/udev/*

import sys
import os
import time
import traceback
import py
import docopt
import logging
from server import config
LOGFILE = config.ROOT.join('log', 'spooler.log')

LP_CONFIG = {
    'drinks': '/dev/usb/lp-thermal',
    'food': '/dev/usb/lp-big',
}


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
    keep_pdf = args['--dev']
    if args['--dev']:
        for key in LP_CONFIG:
            LP_CONFIG[key] = '/dev/tty'
    #
    logging.info('Spooler starting')
    logging.info('spooldir: %s', spooldir)
    #logging.info('printer: %s', printer)
    logging.info('printer: %s', LP_CONFIG)
    html_orders_dir = spooldir.join('orders').ensure(dir=True)
    drinks_dir = spooldir.join('drinks').ensure(dir=True)
    food_dir = spooldir.join('food').ensure(dir=True)
    i = 0
    while True:
        i += 1
        if i % 600 == 0:
            logging.info('I am still alive :)')
        print_html_orders(html_orders_dir, keep_pdf)
        print_receipt(drinks_dir, LP_CONFIG['drinks'])
        print_receipt(food_dir, LP_CONFIG['food'])
        time.sleep(1)

def exec_cmd(cmdline):
    logging.info('EXEC: %s', cmdline)
    ret = os.system(cmdline)
    if ret != 0:
        logging.error('return value: %s', ret)
        return False
    return True

def print_html_orders(orders_dir, keep_pdf):
    print_cmd = 'lp'
    ## if show_pdf:
    ##     print_cmd = 'okular'
    try:
        for html in orders_dir.listdir('*.html'):
            logging.info('Found HTML: %s', html.basename)
            pdf = html.new(ext='pdf')
            if not exec_cmd('wkhtmltopdf --enable-local-file-access --page-size A5 "%s" "%s"' % (html, pdf)):
                continue
            if keep_pdf:
                keep_dir = py.path.local('/tmp/printed_orders').ensure(dir=True)
                pdf.copy(keep_dir)
                html.remove()
                pdf.remove()
            else:
                if not exec_cmd('%s "%s"' % (print_cmd, pdf)):
                    continue
                logging.info('Removing %s and %s', html.basename, pdf.basename)
                html.remove()
                pdf.remove()
    except:
        logging.exception('ERROR!')

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
