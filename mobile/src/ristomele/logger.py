from kivy.logger import Logger as KivyLogger, COLOR_SEQ, RESET_SEQ
YELLOW = 3

def colored(s, color):
    return COLOR_SEQ % (30+color) + s + RESET_SEQ

class MyLogger(object):

    def __init__(self, section):
        self.section = section

    def __getattr__(self, level):
        def fn(message, *args):
            message = '%s: %s' % (self.section, colored(message, YELLOW))
            return getattr(KivyLogger, level)(message, *args)
        return fn

Logger = MyLogger('ristomele')
