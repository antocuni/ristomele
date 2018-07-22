#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import time
from server import config
from server.app import create_app

def run_flask(app):
    """
    Run the app using the builtin flask webserver, for development
    """
    import logging
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    app.run(host='0.0.0.0', debug=True)

def run_cherrypy(app):
    import cherrypy
    from requestlogger import WSGILogger, ApacheFormatter
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
    cherrypy.engine.start()
    cherrypy.engine.block()

def main():
    app = create_app()
    if config.DEBUG:
        print 'WARNING: DEBUG mode enabled'
        run_flask(app)
        #run_cherrypy()
    else:
        run_cherrypy(app)
