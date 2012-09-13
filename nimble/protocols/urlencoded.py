import nimble.protocols.simple as simple
from nimble.protocols.errors import DumpingError
import simplejson
import urllib

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
            path_info = filter(None, self.environ['PATH_INFO'].split('/'))

            if path_info[-1].startswith('p'):
                command = path_info[-2]
            else:
                command = path_info[-1]

            query_string = self.load_post_data()

            if not query_string:
                query_string = self.environ.get('QUERY_STRING', '')

            query_string = urllib.unquote_plus(str(query_string))

            kwargs = dict(item.split('=') for item in query_string.split('&'))

            for key, val in kwargs.items():
                kwargs[key] = simplejson.loads(val)
            print command, kwargs

            return command, (), kwargs

    return ServerConnection

def make_client_connection(BaseConnection):
    BaseConnection = simple.make_client_connection(BaseConnection)

    class ClientConnection(BaseConnection):
        def dump_request(self, data):
            if len(data) == 3:
                command, args, kwargs = data
                return simplejson.dumps({'command': command, 'args': args, 'kwargs': kwargs})
            raise DumpingError('BAD REQUEST DATA')

        def load_response(self, data):
            data = simplejson.loads(data)
            return data['is_error'], data['results']

    return ClientConnection

