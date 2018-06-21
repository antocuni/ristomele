import sys
import os
FORCE_REMOTE = False
if '--remote' in sys.argv:
    FORCE_REMOTE = True
    sys.argv.remove('--remote')

import pypath
import kivy
kivy.require('1.9.1')
from kivy.utils import platform
from bootstrap import Bootstrap, BootstrapApp

if platform == 'android':
    from jnius import autoclass
    env = autoclass('android.os.Environment')
    SDCARD = pypath.local(env.getExternalStorageDirectory().getPath())
    ROOT = SDCARD.join('ristomele')
    local = False
elif FORCE_REMOTE:
    # for testing the remote deployments on the local machine
    ROOT = pypath.local('/tmp/ristomele')
    local = False
else:
    # for local deployments
    ROOT = pypath.local(__file__).dirpath().dirpath()
    local = True


def get_main():
    # check and/or update the source code
    bootstrap = Bootstrap(ROOT, local)
    if bootstrap.update():
        # src updated correctly, load it
        bootstrap.load()
        from ristomele.gui.app import main
        return main
    else:
        # probably we cannot connect to the sync server. Start a simple app to
        # allow the user to change the settings
        return bootstrap_main


def bootstrap_main():
    BootstrapApp(ROOT).run()


if __name__ == '__main__':
    main = get_main()
    if platform == 'android':
        main()
    else:
        try:
            main()
        except:
            import pdb;pdb.xpm()
