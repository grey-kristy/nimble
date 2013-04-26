import functools
import sys
import socket
from nimble.protocols.tools import make_client_connection, DEFAULT_PROTOCOL

def simple_request_over_http(self, shared_name, shared_method):
    @functools.wraps(shared_method)
    def f(*args, **kwargs):
        connection = make_client_connection(self.server, protocol=self.protocol,
                                            secret=self.secret)
        return connection.request(data=(shared_name, args, kwargs))
    return f

class ServerClient(object):
    """
    base class to be used as superclass for 'RPC' client to every nimble server
    parses server object using SERVER_CLASS field to bind the same name wrapper methods to his instance object; such wrappers serialize wrapped function signature to nimble protocol, make sync request over the net and deserialize answer
    """
    SERVER_CLASS = None

    def __init__(self, server, log=None, default_protocol=DEFAULT_PROTOCOL, request_maker=simple_request_over_http, secret=None):
        self.serverobj = self.SERVER_CLASS(log=log)
        self.protocol = default_protocol
        self.server = server
        self.secret = secret

        for nv, meth in self.serverobj._callbacks.items():
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
