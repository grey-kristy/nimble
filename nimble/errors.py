import urllib, traceback, sys
from nimble.tools import object_type, object_type_string

def format_exception(exception, value=None):
    if value is None:
        value = str(exception)
    return '%s: %s'%( object_type_string(exception), value )

class NimbleException(Exception):
    def __init__(self, value=None):
        Exception.__init__(self)

        self.value = value
        self.value = format_exception(self, value)
        if isinstance(value, Exception):
            self.value = format_exception(value)

    def __str__(self):
        return str(self.value)

    def dump(self):
        trace = ''.join(traceback.format_tb(sys.exc_info()[2]))
        t = object_type(self)
        return (t[1], t[0]) + (urllib.quote(trace+str(self)),)

    @classmethod
    def dump_unhandled(cls):
        return ('InternalError',)

    @classmethod
    def load_exception(cls, data):
        e = cls()
        e.value = data
        return e

    @staticmethod
    def load(dumped_exception):
        if len(dumped_exception) > 1:
            try:
                __import__(dumped_exception[1])
                module = sys.modules[dumped_exception[1]]
                cls = getattr(module, dumped_exception[0])
                data = urllib.unquote(dumped_exception[2])
                return cls.load_exception(data)
            except ImportError:
                pass
        return Exception(dumped_exception)

class ConnectionError(NimbleException):
    """
    This error type raised by the problem during connection/unavailability of any points in the connection
    """
class ServerError(NimbleException):
    """
    This error type raised by the bug on the server
    """
class ClientError(NimbleException):
    """
    This error type raised cause of client behaviour
    """
