Overview
=========

There are three main components:

  - the ristomele web server (uwsgi)

  - the ristomele-spooler, which communicates with the printers

  - the kivy client app (android or windows/linux)

To print, ristomele writes to /tmp/spooldir/orders/*.html or
/tmp/spooldir/drinks/*.txt.

ristomele-spooler reads those directories and do the actual print accordingly:

  - orders/*.html are converted to pdf with wkhtmltopdf and sent to the laser
    printer with 'lp'

  - drinks/*.txt are directly sent to the thermal printer, by default
    /dev/usb/lp-thermal (see below)

The DB is stored in ~/ristomele/db.sqlite. It should be manually backed up and
removed every year.



On the raspberry
=================

The uwsgi server is managed by the 'ristomele' systemd service:

$ service ristomele status
● ristomele.service - ristomele uwsgi service
   Loaded: loaded (/etc/systemd/system/ristomele.service; enabled)
   Active: active (running) since Sat 2020-11-07 00:55:56 CET; 1 years 9 months ago
 Main PID: 579 (uwsgi)
   CGroup: /system.slice/ristomele.service
           ├─579 /home/pi/ristomele/venv/bin/uwsgi --ini /home/pi/ristomele/uwsgi.ini
           └─774 /home/pi/ristomele/venv/bin/uwsgi --ini /home/pi/ristomele/uwsgi.ini


The spooler is managed by the 'ristomele-spooler' systemd service:

$ service ristomele-spooler status
● ristomele-spooler.service - ristomele spooler
   Loaded: loaded (/etc/systemd/system/ristomele-spooler.service; enabled)
   Active: active (running) since Sat 2020-11-07 00:55:56 CET; 1 years 9 months ago
 Main PID: 580 (python)
   CGroup: /system.slice/ristomele-spooler.service
           └─580 /home/pi/ristomele/venv/bin/python -m server.spooler /tmp/spooldir/

The services should automatically started on startup. To install the systemd
services, run ~/ristomele/etc/install.sh (should be done only once).

The logs are in ~/ristomele/log:

$ ls -1 ~/ristomele/log/
ristomele.log
spooler.log
uwsgi.log

The web server runs on port 5000. To check that it works, visit the page
(using the appropriate IP address, of course):
   http://192.168.1.6:5000/orders/

lp-thermal
===========

The spooler print drinks by writing to /dev/usb/lp-thermal. This is a symlink
which is automatically created by an UDEV rule, see ~/ristomele/etc/udev.  You
might need to modify the UDEV rule to detect more printers if you use one from
a different manufacturer.

Laser printer / CUPS
====================

The laster printer is managed by CUPS; you can set it up by visting (using the
appropriate IP):

    http://192.168.1.6:631/


Install the app on mobile
===========================

Visit:
    http://192.168.1.6:5000/apk/

If you want to install it manually, the correct apk is the following:

$ md5sum mobile/bin/RistoMele-0.1-debug.apk
6743a4c4c63349cbe9a024685660f6e9  mobile/bin/RistoMele-0.1-debug.apk

$ ls -l --time-style=full mobile/bin/RistoMele-0.1-debug.apk
-rw-r--r-- 1 pi pi 9780426 2018-08-14 16:14:31.249924765 +0200 mobile/bin/RistoMele-0.1-debug.apk


For local development
======================

Start the server by:
  $ python run_server.py


Start the spooler by:
  $ ./run_spooler_dev.sh


Start the app by:
  $ cd mobile/
  $ python launcher/main.py
