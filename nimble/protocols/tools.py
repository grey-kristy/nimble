import nimble.protocols.simple as simple
import nimble.protocols.json as json

from nimble.protocols import wsgi
from nimble.protocols import rabbitmq

DEFAULT_PROTOCOL = json
DEFAULT_CONNECTION_PROTOCOL = wsgi

DEFAULT_PROTOCOL_SELECTOR = {'1': simple, '2': json}
DEFAULT_PROTOCOL_ALIAS_SELECTOR = dict((p, a) for a, p in DEFAULT_PROTOCOL_SELECTOR.items())

def make_server_connection(start_response, environ,
        protocol_selector=DEFAULT_PROTOCOL_SELECTOR,
        connection_protocol=DEFAULT_CONNECTION_PROTOCOL):

    param = environ['PATH_INFO'][-5:]
    protocol = param.startswith('/p:') and protocol_selector[param.rstrip('/')[-1]] \
        or DEFAULT_PROTOCOL

    return protocol.make_server_connection(connection_protocol.ServerConnection)(start_response, environ)

def make_client_connection(server, protocol=DEFAULT_PROTOCOL,
                           protocol_alias_selector=DEFAULT_PROTOCOL_ALIAS_SELECTOR,
                           connection_protocol=DEFAULT_CONNECTION_PROTOCOL,
                           secret=None, queue=None, channel=None):
    connection = protocol.make_client_connection(connection_protocol.ClientConnection)
    if connection_protocol is rabbitmq:
        return connection(channel, queue=queue, secret=secret)
    return connection('%s/p:%s/' % (server, protocol_alias_selector[protocol]), secret=secret)


