import nimble.protocols.simple as simple
import nimble.protocols.json as json

DEFAULT_PROTOCOL = json

DEFAULT_PROTOCOL_SELECTOR = {'1': simple, '2': json}
DEFAULT_PROTOCOL_ALIAS_SELECTOR = dict([(p, a) for a, p in DEFAULT_PROTOCOL_SELECTOR.items()])

def make_server_connection(start_response, environ, protocol_selector=DEFAULT_PROTOCOL_SELECTOR):
    param = environ['PATH_INFO'][-5:]
    if param.startswith('/p:'):
        return protocol_selector[param[-2]].ServerConnection(start_response, environ)
    return DEFAULT_PROTOCOL.ServerConnection(start_response, environ)

def make_client_connection(server, protocol=DEFAULT_PROTOCOL,
                           protocol_alias_selector=DEFAULT_PROTOCOL_ALIAS_SELECTOR, secret=None):
    return protocol.ClientConnection('%s/p:%s/'%(server, protocol_alias_selector[protocol]), secret=secret)

