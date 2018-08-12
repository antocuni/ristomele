#-*- encoding: utf-8 -*-

# NOTE: this file is stored in server/, but also symlinked in
# mobile/src/ristomele

ESC = '\x1b'
CODEPAGE_CP858 = '\x13'

def codepage(cp):
    return ESC + '\x74' + cp

def flags(font_b=False, emph=False, double_height=False, double_width=False,
          underline=False):
    fl = 0
    if font_b: fl ^= 1
    if emph: fl ^= 8
    if double_height: fl ^= 16
    if double_width: fl ^= 32
    if underline: fl ^= 128
    return ESC + '!' + chr(fl)

def big(**kwargs):
    return flags(double_height=True, double_width=True, **kwargs)

def reset():
    return ESC + '@'

def magic_encode(s):
    """
    If given an unicode string, encode it using a suitable codepage and
    prepend the appropriate ESC/POS codepage command, so that the resulting
    string is ready to be printed.
    """
    if isinstance(s, unicode):
        # if we pass an unicode string, we try to encode using cp858, which
        # has at least the Euro symbol. If a character is not available... too
        # bad :(
        s = s.encode('cp858', 'replace')
        cmd = codepage(CODEPAGE_CP858)
        return cmd + s
    else:
        return s


if __name__ == '__main__':
    ## print 'Print modes:'
    ## print 'Font A'
    ## print flags(font_b=True), 'Font B'
    ## print flags(emph=True), 'Emphasized'
    ## print flags(double_height=True), 'Double Height'
    ## print flags(double_width=True), 'Double width'
    ## print big(), 'Big'
    ## print flags(underline=True), 'Underline'
    ## print reset()
    #codepage = '\x1b\x74\x13'
    print codepage(CODEPAGE_CP858)
    print u'Euro: €'.encode('cp858')
    print
    print
