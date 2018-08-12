"""
Usage: spooler/main.py SPOOLDIR -p DEVICE [OPTIONS]

Options:

  -p --printer DEVICE   The device of the printer (e.g. /dev/usb/lp1)
  -h --help             Show help
"""

import sys
import time
import traceback
import py
import docopt


def main():
    args = docopt.docopt(__doc__)
    spooldir = py.path.local(args['SPOOLDIR'])
    printer = py.path.local(args['--printer'])
    #
    if spooldir.check(dir=False):
        print '%s is not a valid directory' % spooldir
        return 1
    if printer.check(exists=False):
        print 'The printer device %s does not exists' % printer
        return 1
    #
    while True:
        for txt in spooldir.listdir('*.txt'):
            print_document(txt, printer)
        time.sleep(1)

def print_document(txt, printer):
    try:
        print 'Printing', txt.basename, '...',
        content = txt.read()
        with printer.open('wb') as f:
            f.write(content)
        txt.remove()
        print 'DONE'
    except:
        print 'ERROR!'
        traceback.print_exc()

if __name__ == '__main__':
    sys.exit(main())
