from Cookie import SimpleCookie
import urllib2, urllib

from nimble.errors import NimbleException
from nimble.client.errors import ServerIsDown
from nimble.tools import LazyProperty

class ServerConnection(object):
    """
    object is created for every request and taken as the first (if no 'self' presented) argument of every nimble server public function (callback)
    """

    STANDART_CONTENT_TYPE = [('Content-Type', 'text/plain'),]
    STANDART_RESPONSE = ('200 OK', STANDART_CONTENT_TYPE)

    def custom_response(self, status):
        return (status, ServerConnection.STANDART_CONTENT_TYPE)

    cookies = LazyProperty(lambda obj, cls: obj.load_cookies())

    def __init__(self, start_response, environ):
        self.environ = environ
        self.start_response = start_response
        self.secret = None

    def dump_response(self, data=None, is_error=False):
        raise NotImplemented

    def HTTP(self, status):
        response = self.get_response_func(status)
        return response("")

    def get_response_func(self, status=None):
        """
        decorating response serializing function with writing WSGI response headers
        @returns:
         @errors:
        """
        if status is None:
            def response(answer):
                self.start_response(*ServerConnection.STANDART_RESPONSE)
                return answer
        else:
            def response(answer):
                self.start_response(*self.custom_response(status))
                return answer
        return response

    def load_post_data(self):
        """
        loading and deserializing nimble protocol request parameters from request environment
        @returns: parameters structure
         @errors:
        """
        if 'CONTENT_LENGTH' not in self.environ:
            # not a POST request
            return ''
        return self.environ['wsgi.input'].read(int(self.environ['CONTENT_LENGTH']))
#        data = data.split('__', 1)
#        self.secret = data[0]
#        return data[1]

    def load_cookies(self):
        try:
            return SimpleCookie(self.environ.get('HTTP_COOKIE', ''))
        except:
            return SimpleCookie('')

    def load_file(self, environ):
        """
        loading file data from request environment
        @returns: sent file name, sent file data
         @errors:
        """

        data = self.load_post_data()
        #TODO: rewrite all        
        starttag = '\r\n\r\n'
        endtag = '\r\n--'
        start = data.index(starttag) # Exception!
        start += len(starttag)
        end = data.rindex(endtag) #Exception!

        fname = data[data.index('filename="')+len('filename="'):start] #Exception!
        fname = fname[:fname.index('"')]
        
        fdata = data[start:end]

        return fname, fdata

class ClientConnection(object):
    def __init__(self, server, secret=None):
        self.server = server
        self.secret = secret

    def load_response(self, data):
        raise NotImplemented

    def dump_request(self, data):
        raise NotImplemented

    def request(self, data):
        post_body = self.dump_request(data)
        try:
            if not post_body:
                raw_data = urllib2.urlopen(self.server).read()
            else:
                raw_data = urllib2.urlopen(self.server, data=post_body).read()
        except urllib2.HTTPError, ex:
            raise ServerIsDown('%s: %s'%(self.server, ex))

        isError, returnValues = self.load_response(raw_data)
        if isError:
            raise NimbleException.load(returnValues)
        
        return returnValues

