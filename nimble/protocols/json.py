import nimble.protocols.simple as simple
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
            return data['command'], data['args']
    return ServerConnection

def make_client_connection(BaseConnection):
    BaseConnection = simple.make_client_connection(BaseConnection)

    class ClientConnection(simple.ClientConnection):
        def dump_request(self, data):
            command, args = data
            return simplejson.dumps({'command': command, 'args': args})

        def load_response(self, data):
            data = simplejson.loads(data)

            return data['is_error'], data['results']
    return ClientConnection

