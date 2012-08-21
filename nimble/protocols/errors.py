from nimble.tools import object_type_string
from nimble.errors import NimbleException

class ProtocolProcessingError(NimbleException):
    def __init__(self, connection, message):
        if connection is None and message is None:
            value = None
        else:
            value = '%s: %s'%(object_type_string(connection), message)
        NimbleException.__init__(self, value)

    @classmethod
    def load_exception(cls, data):
        e = cls(None, None)
        e.value = data
        return e

class DumpingError(ProtocolProcessingError): pass
class LoadingError(ProtocolProcessingError): pass
