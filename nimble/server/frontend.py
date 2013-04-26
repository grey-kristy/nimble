import functools

class GEventServer(object):
    def __init__(self, address, application, application_shutdown, **opts):
        import gevent.wsgi
        self.server = gevent.wsgi.WSGIServer
        self.application = application
        self.setup_signals(application_shutdown)
        self.address = address
        self.opts = opts

    def loop(self):
        #TODO:
        backlog = 256
        if 'backlog' in self.opts:
            backlog = self.opts['backlog']
            del self.opts['backlog']
        server = self.server(self.address, self.application, **self.opts)
        server.backlog = backlog
        server.serve_forever()

    def setup_signals(self, application_shutdown):
        import gevent, signal
        application_shutdown = functools.partial(application_shutdown, signum=None, frame=None)
        gevent.signal(signal.SIGTERM, application_shutdown)
        gevent.signal(signal.SIGQUIT, application_shutdown)

class FlupServer(object):
    def __init__(self, address, application, application_shutdown, **opts):
        import flup.server.fcgi
        self.server = flup.server.fcgi.WSGIServer
        self.application = application
        self.setup_signals(application_shutdown)
        self.address = address
        self.opts = opts

    def loop(self):
        server = self.server(self.application, bindAddress=self.address, **self.opts)
        server.run()

    def setup_signals(self, application_shutdown):
        import signal
        signal.signal(signal.SIGTERM, application_shutdown)

ALL = {
    'flup': FlupServer,
    'gevent': GEventServer,
}

DEFAULT = GEventServer
