#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import argparse
import os
import subprocess
from server import config
from server.app import create_app

# Paths for the self-signed TLS certificate, stored next to this file.
_HERE = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(_HERE, 'ssl_cert.pem')
KEY_FILE  = os.path.join(_HERE, 'ssl_key.pem')


def ensure_ssl_cert():
    """Generate a self-signed cert/key pair if they don't already exist."""
    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        return
    print 'Generating self-signed TLS certificate...'
    subprocess.check_call([
        'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
        '-keyout', KEY_FILE,
        '-out',    CERT_FILE,
        '-days',   '3650',
        '-nodes',
        '-subj',   '/CN=ristomele',
    ])
    print 'Certificate written to', CERT_FILE


def run_flask_dev(app):
    """HTTP + reloader, for development (no Bluetooth)."""
    import logging
    logging.basicConfig()
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    print 'Listening on http://localhost:5000  (dev mode, no Bluetooth)'
    app.run(host='0.0.0.0', debug=True)

def run_flask_https(app):
    """HTTPS without reloader — required for Web Bluetooth in the JS client."""
    import logging
    logging.basicConfig()
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    ensure_ssl_cert()
    print 'Listening on https://localhost:5000'
    # use_reloader=False: werkzeug reloader forks the process and breaks SSL
    app.run(host='0.0.0.0', debug=True, use_reloader=False,
            ssl_context=(CERT_FILE, KEY_FILE))

def run_cherrypy(app):
    import cherrypy
    from requestlogger import WSGILogger, ApacheFormatter
    ensure_ssl_cert()
    #
    # main app
    logged_app = WSGILogger(app, app.logger.handlers, ApacheFormatter())
    cherrypy.tree.graft(logged_app, '/')
    #
    # serve static files
    cherrypy.tree.mount(None, '/static', config={
        '/': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': app.static_folder
        },
    })
    #
    # run server
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.config.update({'server.socket_port': 5000})
    cherrypy.server.ssl_certificate = CERT_FILE
    cherrypy.server.ssl_private_key = KEY_FILE
    cherrypy.engine.start()
    cherrypy.engine.block()

def main():
    app = create_app()
    if not config.DEBUG:
        run_cherrypy(app)
        return

    parser = argparse.ArgumentParser(description='RistoMele server (DEBUG mode)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--dev',
        action='store_true',
        help='HTTP with auto-reloader (fast iteration; Web Bluetooth not available)',
    )
    group.add_argument(
        '--https',
        action='store_true',
        help='HTTPS without reloader (enables Web Bluetooth in the JS client)',
    )
    args = parser.parse_args()
    if args.dev:
        run_flask_dev(app)
    else:
        run_flask_https(app)
