import datetime, cStringIO, functools, operator

from nimble.errors import NimbleException
from nimble.tools import object_type_string
from nimble.client.base import ServerClient
from nimble.protocols.tools import make_client_connection

NOW = datetime.datetime.now

#test no error raising
def test(func):
    func_name = func.__name__
    def f(*args, **kwargs):
        try:
            res, t, data = func(*args, **kwargs)
            print _ok_str(func_name, t, data, res)
            return res
        except NimbleException, ex:
            print _err_str(func_name, 'Server return error: %s'%ex)
    return f

#test on error raising
def test_fail(func):
    func_name = func.__name__
    def f(*args, **kwargs):
        try:
            res, t, data = func(*args, **kwargs)
            print _err_str(func_name, res, True)
        except NimbleException, ex:
            print _ok_str(func_name, None, None, object_type_string(ex), True)
    return f

#test comparing the result with params
def expect_result(expected_result, cmp=operator.eq):
    def decorator(func):
        func_name = func.__name__
        def f(*args, **kwargs):
            try:
                res, t, data = func(*args, **kwargs)
                if cmp(res, expected_result):
                    print _ok_str(func_name, t, data, res)
                    return res
                else:
                    print _err_str(func_name, '%s != %s'%(expected_result, res))
            except NimbleException, ex:
                print _err_str(func_name, 'Server return error: %s'%ex)
        return f
    return decorator
   
def _err_str(func_name, res, fail=False, fullInfo=True):
    scheme = 'ERROR: %s'
    params = [func_name]
    if fail:
        scheme = 'ERROR (NO FAIL): %s'
    if fullInfo:
        scheme += ': %s'
        params.append(res)
    return scheme%tuple(params)

def _ok_str(func_name, t, data, res, fail=False, fullInfo=True):
    scheme = 'SUCCESS (%s): %s'
    params = [t, func_name]
    if fail:
        scheme = 'SUCCESS ON FAIL (%s): %s'
    if fullInfo:
        scheme += ': %s'
        params.append(res)
    return scheme%tuple(params)

def direct_call(server, data, path_info):
    environ = {'REMOTE_ADDR': '0.0.0.0'}
    environ['PATH_INFO'] = path_info
    environ['CONTENT_LENGTH'] = 2*len(data)-1
    environ['wsgi.input'] = cStringIO.StringIO(data)

    t0 = NOW()
    res = server.process_request(lambda x,y:x, environ)
    t = NOW()-t0
    return res, t

def simple_request_over_direct_call(self, shared_name, shared_method):
    @functools.wraps(shared_method)
    def f(*args, **kwargs):
        connection = make_client_connection(server=None)
        postBody = connection.dump_request(data=(shared_name, args, kwargs))
        response, t = direct_call(self.serverobj, postBody, connection.server)
        isError, answer = connection.load_response(response)
        if isError:
            raise NimbleException.load(answer)
        return answer, t, postBody
    return f

class TestLogger(object):
    def debug(self, msg):
        print 'SERVER LOG: %s'%msg

class TestingClient(ServerClient):
    def __init__(self, serverClass):
        self.SERVER_CLASS = serverClass

        print 'rescode (overheaded time): name: additional info'
        print '--------------------------------------------'
        connection = make_client_connection(server=None)
        print 'server is tested with connection: %s'%object_type_string(connection)
        print '--------------------------------------------'

        ServerClient.__init__(self, server=None, log=TestLogger(), request_maker=simple_request_over_direct_call)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.serverobj.shutdown()