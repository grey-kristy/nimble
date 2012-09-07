import functools
import socket
from nimble.protocols.tools import make_client_connection, DEFAULT_PROTOCOL

def simple_request_over_http(self, shared_name, shared_method):
    @functools.wraps(shared_method)
    def f(*args):
        connection = make_client_connection(self.server, protocol=self.protocol,
                                            secret=self.secret)
        returnValues = connection.request(data=(shared_name, args))

        return returnValues
    return f

class ServerClient(object):
    """
    base class to be used as superclass for 'RPC' client to every nimble server
    parses server object using SERVER_CLASS field to bind the same name wrapper methods to his instance object; such wrappers serialize wrapped function signature to nimble protocol, make sync request over the net and deserialize answer
    """
    SERVER_CLASS = None

    def __init__(self, server, default_protocol=DEFAULT_PROTOCOL, request_maker=simple_request_over_http, secret=None):
        serverobj = self.SERVER_CLASS()
        self.protocol = default_protocol
        self.server = server
        self.secret = secret

        for nv, meth in serverobj._callbacks.items():
            f = request_maker(self, shared_name=nv, shared_method=meth)
            setattr(self, meth.__name__, f)

class StandaloneClient(object):
     def __init__(self, server, default_protocol=DEFAULT_PROTOCOL, request_maker=simple_request_over_http, secret=None):
        self.protocol = default_protocol
        self.server = server
        self.secret = secret

        empty = lambda: None
        f = request_maker(self, shared_name="", shared_method=empty)
        signatures = f()

        for meth_name in signatures:
            f = request_maker(self, shared_name=meth_name, shared_method=empty)
            setattr(self, meth_name, f)


def simple_publisher(self, shared_name, shared_method, channel, queue):
    from nimble.protocols import rabbitmq
    @functools.wraps(shared_method)
    def f(*args):
        connection = make_client_connection(None, channel=self.channel, protocol=self.protocol,
                                            secret=self.secret, connection_protocol=rabbitmq, queue=queue)
        connection.publish(data=(shared_name, args))
    return f

class MQClient(object):
    queue = None
    SERVER_CLASS = None

    def __init__(self, queue=None, server_class=None, default_protocol=DEFAULT_PROTOCOL, secret=None):
        queue = queue or self.queue
        self.queue = queue
        self.protocol = default_protocol
        self.secret = secret

        try:
            self._init_send_mq()
        except socket.error as e:
            print "Can't connect to RabbitMQ: %s" % e
            #log.error("Can't connect to RabbitMQ: %s" % e)
            sys.exit(1)

        server_class = server_class or SERVER_CLASS
        serverobj = server_class()

        for nv, meth in serverobj._callbacks.items():
            f = simple_publisher(self, shared_name=nv, shared_method=meth,
                channel=self.channel, queue=queue)
            setattr(self, meth.__name__, f)

    def _init_send_mq(self):
        import pika
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue)
