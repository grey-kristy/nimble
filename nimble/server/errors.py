from nimble.errors import ConnectionError, ClientError

class PermissionDenied(ClientError):
    """
    This error type raised cause of unauthorized access
    """
class InvalidParams(ClientError):
    """
    This error type raised cause of bad parameter value or bad parameters number
    """
class InvalidOperation(ClientError):
    """
    This error type raised cause in the current state operation request is invalid
    """
class ServerIsBusy(ConnectionError):
    """
    This error type raised cause server can't response in the current state
    """
