import functools
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

