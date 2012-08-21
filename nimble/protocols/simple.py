import nimble.protocols.wsgi as wsgi
from nimble.protocols.errors import DumpingError

class ServerConnection(wsgi.ServerConnection):
    LIST_TYPES = (list, tuple)

    _OK = ("OK", "OK\n%s")
    _ERR = ("ERROR", "ERROR\n%s")

    def _process_list(self, data, tmpl):
        if isinstance(data[0], self.LIST_TYPES):
            return tmpl%('\n'.join([' '.join(p) for p in data]))
        return tmpl%(' '.join(data))

    def _process_dict(self, data, tmpl):
        return tmpl%('\n'.join([' '.join(p) for p in data.items()]))

    def dump_response(self, data=None, is_error=False):
        """
        serializing function results to simple protocol
        @returns: string representation
         @errors:
        """
        if is_error:
            tmpl_s, tmpl_m = self._ERR
        else:
            tmpl_s, tmpl_m = self._OK

        if data is None:
            return tmpl_s
        try:
            if isinstance(data, self.LIST_TYPES):
                return self._process_list(data, tmpl_m)
            if isinstance(data, dict):
                return self._process_dict(data, tmpl_m)
        except TypeError:
            raise DumpingError(self, """Some of your data items or structures are not of a stringable type.
Please manually convert all data items to string before dumping to protocol. Or switch protocol.
Your data: %s"""%repr(data))
        return tmpl_m%data

    def OK(self, x=None):
        response = self.get_response_func()
        return response(self.dump_response(x))

    def ERROR(self, x=None):
        response = self.get_response_func()
        return response(self.dump_response(x, True))

    def load_request(self):
        """
        loading and deserializing simple protocol request parameters from request environment
        @returns: parameters structure
         @errors:
        """
        data = self.load_post_data().split(' ')
        return data[0], data[1:]

class ClientConnection(wsgi.ClientConnection):
    def dump_request(self, data):
        """
        serializing function call into the nimble protocol using function alias 'command' and function arguments
        @returns: string representation
         @errors: InvalidParams
        """
        command, args = data
        if not args:
            return command
        return "%s %s"%(command, ' '.join([str(a) for a in args]))

    def load_response(self, data):
        """
        deserializing function answer from nimble protocol
        @returns: function error status (True/False), 2D matrix of function results
         @errors:
        """
        r = data.split('\n')
        is_error = True if r[0]=='ERROR' else False
        data = r[1:]

        if not data:
            return is_error, None

        #TODO: protocol bug
        if len(data) == 1:
            res = data[0].split(' ')
            if len(res) == 1:
                return is_error, data[0]
            return is_error, res

        return is_error, tuple([tuple(l.split(' ')) for l in data])

