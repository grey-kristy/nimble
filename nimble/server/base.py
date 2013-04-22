import sys
import codecs
import daemon
import traceback

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

    @classmethod
    def application(cls, environ, start_response):
        return cls.singleton.process_request(start_response, environ)

    @classmethod
    def run(cls, ip='127.0.0.1', port=9000, secret=None, auth_id=None, debug=False,
            stderr=None, stdout=None,
            frontend_server=frontend.DEFAULT, **frontend_opts):
        if cls.singleton is None:
             cls.singleton = cls(ip=ip, port=port, secret=secret, auth_id=auth_id)

        stderr_fd = stdout_fd = None
        if stderr is not None:
            stderr_fd = codecs.open(stderr, 'a+', 'utf-8')
            sys.stderr = stderr_fd
        if stdout is not None:
            stdout_fd = codecs.open(stderr, 'a+', 'utf-8')
            sys.stdout = stdout_fd

        try:
            frontend_server(address=(ip,port), application=cls.application,
                        **frontend_opts).loop()
        except:
            print >> sys.stderr, 'frontend failed:', traceback.format_exc()
        finally:
            if stdout_fd:
                stdout_fd.close()
            if stderr_fd:
                stderr_fd.close()

    @classmethod
    def run_daemon( cls, ip='127.0.0.1', port=9000, secret=None, auth_id=None, pidfile=None,
                    fullLoadBeforeStart=False, debug=False,
                    stderr=None, stdout=None,
                    frontend_server=frontend.FlupServer, **frontend_opts):
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

            elif arg.startswith('ip='):
                ip = arg.split('=')[1]

            elif arg.startswith('secret='):
                secret = arg.split('=')[1]

            elif arg.startswith('auth_id='):
                auth_id = arg.split('=')[1]

            elif arg.startswith('frontend='):
                frontend_server=frontend.ALL[arg.split('=')[1]]

            elif arg.startswith('queue='):
                frontend_opts['queue'] = arg.split('=')[1]

            elif arg.startswith('stderr='):
                stderr = arg.split('=')[1]
            elif arg.startswith('stdout='):
                stdout = arg.split('=')[1]

            else:
                opt, val = arg.split('=')
                frontend_opts[opt] = eval(val)

        run_kwargs = dict(ip=ip, port=port, secret=secret, auth_id=auth_id,
                          stderr=stderr, stdout=stdout,
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
            print >> sys.stderr, "usage: %s start|stop|restart|debug [option=value]" % sys.argv[0]
            sys.exit(2)

        print "using: address: %s%s," % (ip, port and (':%s' % port) or ''),
        print "frontend:", frontend_server
        actions[sys.argv[1]]()

        sys.exit(0)

    @shared
    def _get_signatures_(self, connection):
        res = self._callbacks.keys()
        res.remove('_get_signatures_')
        return connection.OK(res)

    #no net-specific calls are allowed, because there's no net environment or binded sockets at this moment
    def __init__(self, ip=None, port=None, secret=None, auth_id=None):
        self.secret = secret
        self.ip = ip
        self.port = port
        self.auth = Auth(auth_id, None)
        self.logfile = self.__class__.__name__
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
            return connection.ERROR([traceback.format_exc()])
            #command, params, keyword_params = "_get_signatures_", [], {}

        if command not in self._callbacks:
            msg = 'No such command: %s' % command
            return connection.ERROR([msg])
        res = self._callbacks[command](connection, *params, **keyword_params)
        return res

    def process_upload_request(self, start_response, environ):
        connection = make_server_connection(start_response, environ,
            connection_protocol=self.connection_protocol)
        filename, filedata = connection.load_file()

        return self._callbacks[command](connection, filename, filedata)
