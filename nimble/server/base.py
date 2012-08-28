import sys
import daemon

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
            frontend_server=frontend.DEFAULT, **frontend_opts):
        if cls.singleton is None:
             cls.singleton = cls(ip=ip, port=port, secret=secret, auth_id=auth_id)
        frontend_server(address=(ip,port), application=cls.application,
                        **frontend_opts).loop()

    @classmethod
    def run_daemon( cls, ip='127.0.0.1', port=9000, secret=None, auth_id=None, pidfile=None, fullLoadBeforeStart=False,
                    debug=False, frontend_server=frontend.FlupServer, **frontend_opts):
        for arg in sys.argv[2:]:
            if arg.startswith('port='):
                port = int(arg.split('=')[1])
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
            else:
                opt,val=arg.split('=')
                frontend_opts[opt]=eval(val)
        
        run_method = lambda: cls.run(ip=ip, port=port, secret=secret, auth_id=auth_id,
                                     debug=debug, frontend_server=frontend_server,
                                     **frontend_opts)

        class MyDaemon(daemon.Daemon):
            def run(self):
                run_method()

        pidfile = '/tmp/daemon_%s.pid'%cls.__name__ if not pidfile else pidfile
        d = MyDaemon(pidfile)

        def loadable(func):
            def f():
                #makes an opportunity to load everything just before shutting down last instance or to invoke init before any real work
                # if fullLoadBeforeStart:
                #     cls.get_instance(secret=secret, auth_id=auth_id, port=port, ip=ip)
                return func()
            return f

        actions = {'start': loadable(d.start), 'stop': d.stop,
                   'restart': loadable(d.restart),
                   'debug': loadable(run_method) }

        if len(sys.argv) < 2 or sys.argv[1] not in actions.keys():
            print "usage: %s start|stop|restart|debug [option=value]" % sys.argv[0]
            sys.exit(2)

        print "using: address: %s %s, frontend: %s"%(ip, port, frontend_server)
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
        #TODO: bad design
        self.clientMode = not self.ip and not self.port

        self._callbacks = get_shared(self)

    def process_request(self, start_response, environ):
        connection = make_server_connection(start_response, environ)
        try:
            command, params = connection.load_request()
        except:
            command, params = "_get_signatures_", []

        return self._callbacks[command](connection, *params)

    def process_upload_request(self, start_response, environ):
        connection = make_server_connection(start_response, environ)
        filename, filedata = connection.load_file()

        return self._callbacks[command](connection, filename, filedata)
