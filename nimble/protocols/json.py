import nimble.protocols.simple as simple
from nimble.protocols.errors import DumpingError
import simplejson

def make_server_connection(BaseConnection):
    NewBaseConnection = simple.make_server_connection(BaseConnection)
    
    class ServerConnection(NewBaseConnection):
        def dump_response(self, data=None, is_error=False):
            """
            serializing function results to json protocol
            @returns: string representation
             @errors:
            """
            return simplejson.dumps({'is_error': is_error, 'results': data})

        def load_request(self):
            data = simplejson.loads(self.load_post_data(), encoding='utf8')
            if 'kwargs' in data:
                return data['command'], data['args'], data['kwargs']
            return data['command'], data['args']
    return ServerConnection

def make_client_connection(BaseConnection):
    BaseConnection = simple.make_client_connection(BaseConnection)

    class ClientConnection(BaseConnection):
        def dump_request(self, data):
            if len(data) == 2:
                command, args = data
                return simplejson.dumps({'command': command, 'args': args})
            elif len(data) == 3:
                command, args, kwargs = data
                return simplejson.dumps({'command': command, 'args': args, 'kwargs': kwargs})
            raise DumpingError('BAD REQUEST DATA')
            

        def load_response(self, data):
            data = simplejson.loads(data)

            return data['is_error'], data['results']
    return ClientConnection

