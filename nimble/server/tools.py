import sys, traceback
import functools, inspect, urllib
from nimble.errors import NimbleException, ServerError
from nimble.server.errors import PermissionDenied

SHARED_AS_PROPERTY = '_nimble_shared_as'

### Special decorators for shared methods declaration-style
def process_exceptions(func):
    """
    decorating server public function (callback) with catching and processing exceptions to nimble protocol errors
    @returns: decorated function
     @errors: PermissionDenied
    """
    @functools.wraps(func)
    def f(self, connection, *args, **kwargs):
        try:
            return func(self, connection, *args, **kwargs)
        except NimbleException, ex:
            traceback.print_exc()
            return connection.ERROR(ex.dump())
        except Exception, ex:
            traceback.print_exc()
            return connection.ERROR(ServerError(ex).dump())
        except:
            traceback.print_exc()
            return connection.ERROR(NimbleException.dump_unhandled())
    return f

def shared(func):
    setattr(func, SHARED_AS_PROPERTY, func.__name__)
    return process_exceptions(func)

def shared_as(alias):
    def decorator(func):
        setattr(func, SHARED_AS_PROPERTY, alias)
        return process_exceptions(func)
    return decorator

def get_shared(server_instance):
    predicate = lambda m: inspect.ismethod(m) and hasattr(m, SHARED_AS_PROPERTY)
    shared = inspect.getmembers(server_instance, predicate)
    return dict([(getattr(m, SHARED_AS_PROPERTY), m) for n, m in shared])

### Authorization

def default_auth_error_handler(self):
    raise PermissionDenied('Not authorized')

class Auth(object):
    def __init__(self, id_, data):
        self.id = id_
        self.data = data

def default_auth_success_handler(self, connection, auth_id, auth_data):
    setattr(connection, 'auth', Auth(auth_id, auth_data))

#auth decorator factory for general authorization
def make_auth_required(identity_func,
                       on_success = default_auth_success_handler,
                       on_error = default_auth_error_handler):
    """
    creates authorization decorator by
        identity_func: get_user_id_from_connection(connection)
        optional on_success callback: do_on_auth_success(self, connection, userid), by default 
            modifies connection object by adding userid and userdata fields to it
        optional on_error callback: do_on_auth_error(self), by default
            raises PermissionDenied exception
    """
    def decorator(func):
        @functools.wraps(func)
        def f(self, connection, *args, **kwargs):
            auth_id, auth_data = identity_func(connection)
            if not auth_id:
                return on_error(self)

            on_success(self, connection, auth_id, auth_data)
            return func(self, connection, *args, **kwargs)
        return f
    return decorator

def secret_check_required(func):
    @functools.wraps(func)
    def f(self, connection, secret, *args, **kwargs):
        if secret != self.secret:
            raise PermissionDenied('Untrusted source')
        return func(self, connection, *args, **kwargs)
    return f

def make_ip_auth(ip_list):
    '''Create authorization decorator by list of trusted IP address
    example of usage:
    ip_auth = make_ip_auth(['127.0.0.1', '192.168.1.1'])

    @ip_auth
    @shared
    def my_handler(self, connection):
        ...
    '''
    def cover(func):
        def decorator(self, connection, *args, **kwargs):
            real_ip = connection.environ.get('HTTP_X_REAL_IP')
            for ip in ip_list:
                if ip == real_ip:
                    return func(self, connection, *args, **kwargs)
            return connection.ERROR(['Untrusted IP: %s' % real_ip])
#            raise PermissionDenied('Untrusted IP: %s' % real_ip)
        return functools.wraps(func)(decorator)
    return cover
