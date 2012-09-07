from Cookie import SimpleCookie
import urllib2, urllib

from nimble.errors import NimbleException
from nimble.client.errors import ServerIsDown
from nimble.tools import LazyProperty

class ServerConnection(object):
    """
    object is created for every request and taken as the first (if no 'self' presented) argument of every nimble server public function (callback)
    """

    #STANDART_CONTENT_TYPE = [('Content-Type', 'text/plain'),]
    #STANDART_RESPONSE = ('200 OK', STANDART_CONTENT_TYPE)

    #def custom_response(self, status):
    #    return (status, ServerConnection.STANDART_CONTENT_TYPE)

    cookies = LazyProperty(lambda obj, cls: obj.load_cookies())

    def __init__(self, start_response, environ):
        self.environ = environ
        self.start_response = start_response
        self.secret = None
        print "RabbitMQ ServerConnection initialized"

    def dump_response(self, data=None, is_error=False):
        raise NotImplemented

    def HTTP(self, status):
        raise NotImplemented

    def get_response_func(self, status=None):
        return lambda answer: answer

    def load_post_data(self):
        """
        loading and deserializing nimble protocol request parameters from request environment
        @returns: parameters structure
         @errors:
        """
        return self.environ['body']

    def load_cookies(self):
        return {}

    def load_file(self, environ):
        raise NotImplemented

class ClientConnection(object):
    def __init__(self, channel, queue, secret=None):
        self.channel = channel
        self.secret = secret
        self.queue = queue

    def load_response(self, data):
        raise NotImplemented

    def dump_request(self, data):
        raise NotImplemented

    def publish(self, data):
        body = self.dump_request(data)
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=body)


