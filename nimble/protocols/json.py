from nimble.protocols import simple
from nimble.protocols.errors import DumpingError

def import_non_local(name, custom_name=None):
    import imp, sys

    custom_name = custom_name or name

    f, pathname, desc = imp.find_module(name, sys.path[1:])
    module = imp.load_module(custom_name, f, pathname, desc)

    return module

try:
    # Try to import stdlib json
    simplejson = import_non_local('json', 'std_json')
except ImportError:
    import simplejson

class ServerConnection(simple.ServerConnection):
    def dump_response(self, data=None, is_error=False):
        """
        serializing function results to json protocol
        @returns: string representation
         @errors:
        """
        return simplejson.dumps({'is_error': is_error, 'results': data})

    def load_request(self):
        data = simplejson.loads(self.load_post_data(), encoding='utf8')
        return data['command'], data['args'], data.get('kwargs', {})


class ClientConnection(simple.ClientConnection):
    def dump_request(self, data):
        command, args, kwargs = data
        return simplejson.dumps({'command': command, 'args': args, 'kwargs': kwargs})
        

    def load_response(self, data):
        data = simplejson.loads(data)

        return data['is_error'], data['results']


