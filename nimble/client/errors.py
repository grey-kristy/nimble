from nimble.errors import ServerError, ConnectionError

class ServerIsDown(ConnectionError):
    """
    This error type raised cause target server is unreachable
    """
