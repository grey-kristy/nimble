
class GEventServer(object):
    def __init__(self, address, application, **opts):
        import gevent.wsgi
        self.server = gevent.wsgi.WSGIServer
        self.application = application
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

    def multicore_loop(self):
       import sys
       from gevent.socket import create_connection
       from gevent import wsgi
       from multiprocessing import Process, current_process, cpu_count

       listener = create_connection(self.address)

       def serve_forever(listener):
           self.server(listener, self.application, backlog=1024, **self.opts).serve_forever()

       number_of_processes = cpu_count()-1
       print 'Starting %s processes' % number_of_processes
       for i in range(number_of_processes):
           procs.append(Process(target=serve_forever, args=(listener,)))

       for p in procs:
           p.start()

       serve_forever(listener)
       for p in procs:
           p.join()

class FlupServer(object):
    def __init__(self, address, application, **opts):
        import flup.server.fcgi
        self.server = flup.server.fcgi.WSGIServer
        self.application = application
        self.address = address
        self.opts = opts

    def loop(self):
        server = self.server(self.application, bindAddress=self.address, **self.opts)
        server.run()

ALL = {'flup': FlupServer,
       'gevent': GEventServer}
DEFAULT = FlupServer
