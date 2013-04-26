import sys, os
import codecs
import daemon
import traceback
import signal

import logging

def get_log_handler(fname):
    handler = logging.FileHandler(fname, 'a', 'utf-8')
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(module)s %(message)s",
                                  "%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    return handler

from nimble.server.tools import get_shared, shared, Auth
import nimble.server.frontend as frontend
from nimble.protocols.tools import make_server_connection

class Server(object):
    """
    base class to be used as superclass for every nimble server
    aggregates: 
        *nix daemon management (including cmd), 
        WSGI processing as a 'flup' application, 
        request deserializing, 
        public functions calls management through callback system
    """

    singleton = None
    is_running = False

    @classmethod
    def application(cls, environ, start_response):
        return cls.singleton.process_request(start_response, environ)

    @classmethod
    def server_shutdown(cls):
        if cls.singleton.is_running:
            cls.singleton.is_running = False
            cls.singleton.log.debug('Server is going to shutdown')
            try:
                return cls.singleton.shutdown()
            except Exception as e:
                cls.singleton.log.debug('Server shutdown: %s'%e)

    @classmethod
    def run(cls, ip='127.0.0.1', port=9000, debug=False, log_dir=None,
            frontend_server=None, **frontend_opts):

        log = logging.getLogger('nimble')
        log.setLevel(logging.DEBUG)
        log.addHandler(get_log_handler('%s/nimble.log'%log_dir))

        if cls.singleton is None:
            try:
                cls.singleton = cls(ip=ip, port=port, log=log, log_dir=log_dir)
            except Exception, e:
                cls.singleton.log.debug('Server init failed: %s'%e)
                raise
        cls.singleton.log.debug('Server initialized')

        def abort(signum, frame):
            cls.server_shutdown()

        try:
            cls.is_running = True
            frontend_server(address=(ip,port), application=cls.application,
                            application_shutdown=abort,
                            **frontend_opts).loop()
        except:
            cls.singleton.log.debug('Frontend failed: %s'%traceback.format_exc())
            raise

    @classmethod
    def run_daemon( cls, ip='127.0.0.1', port=9000, pidfile=None, log_dir=None,
                    debug=False, frontend_server=None, **frontend_opts):
        #print 'run_daemon', cls
        for arg in sys.argv[2:]:
            if arg.startswith('port='):
                port = arg.split('=')[1]
                if port.lower() == 'none':
                    port = None
                else:
                    port = int(port)
            elif arg.startswith('pidfile='):
                pidfile = arg.split('=')[1]

            elif arg.startswith('log_dir='):
                log_dir = arg.split('=')[1]

            elif arg.startswith('ip='):
                ip = arg.split('=')[1]

            elif arg.startswith('frontend='):
                frontend_server=frontend.ALL[arg.split('=')[1]]

            else:
                opt, val = arg.split('=')
                frontend_opts[opt] = eval(val)

        run_kwargs = dict(ip=ip, port=port, log_dir=log_dir,
                          debug=debug, frontend_server=frontend_server)
        run_kwargs.update(frontend_opts)
        run_method = lambda: cls.run(**run_kwargs)

        class MyDaemon(daemon.Daemon):
            def run(self):
                run_method()

        pidfile = '/tmp/daemon_%s.pid' % cls.__name__ if not pidfile else pidfile
        d = MyDaemon(pidfile)

        actions = {
            'start': d.start,
            'stop': d.stop,
            'restart': d.restart,
            'debug': run_method
        }

        if len(sys.argv) < 2 or sys.argv[1] not in actions:
            print "usage: %s start|stop|restart|debug [option=value]" % sys.argv[0]
            sys.exit(2)

        print "using: address: %s%s," % (ip, port and (':%s' % port) or ''),
        print "frontend:", frontend_server

        try:
            actions[sys.argv[1]]()
        except KeyboardInterrupt:
            cls.singleton.shutdown()

        sys.exit(0)

    @shared
    def _get_signatures_(self, connection):
        res = self._callbacks.keys()
        res.remove('_get_signatures_')
        return connection.OK(res)

    #no net-specific calls are allowed, because there's no net environment or binded sockets at this moment
    def __init__(self, ip=None, port=None, log=None, log_dir=''):
        self.ip = ip
        self.port = port
        self.log = log
        self.log_dir = log_dir or os.getcwd()+'/logs/'
        self.is_running = True
        
        #TODO: bad design
        self.clientMode = not self.ip and not self.port

        self._callbacks = get_shared(self)

    def process_request(self, start_response, environ):
        connection = make_server_connection(start_response, environ)
        
        try:
            data = connection.load_request()
            command, params, keyword_params = data
            if not command:
                command = "_get_signatures_"
        except Exception as ex:
            return connection.ERROR(['Incorrect request: %s'%traceback.format_exc()])
            #command, params, keyword_params = "_get_signatures_", [], {}

        try:
            callback = self._callbacks[command]
        except KeyError, e:
            return connection.ERROR(['No such command: %s' % command])

        try:
            return callback(connection, *params, **keyword_params)
        except:
            return connection.ERROR(['Server return: %s'%traceback.format_exc()])

    def process_upload_request(self, start_response, environ):
        connection = make_server_connection(start_response, environ,
            connection_protocol=self.connection_protocol)
        filename, filedata = connection.load_file()

        return self._callbacks[command](connection, filename, filedata)

    def shutdown(self):
        pass
