#!/usr/bin/env python2.6

from nimble.server.base import Server
from nimble.client.base import ServerClient
from nimble.server.tools import shared, shared_as

class TestServer(Server):
    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)

        self.value = None

    @shared
    def load(self, connection, value):
        value = int(value)
        self.value = value

        return connection.OK()

    @shared_as('+')
    def add(self, connection, valueToAdd):
        valueToAdd = int(valueToAdd)
        self.value += valueToAdd

        return connection.OK(str(self.value))

    @shared_as('/')
    def divide(self, connection, valueToDivide):
        valueToDivide = int(valueToDivide)
        self.value = int(self.value/valueToDivide)

        return connection.OK(str(self.value))

class TestServerClient(ServerClient):
    SERVER_CLASS = TestServer

if __name__=='__main__':
    TestServer.run_daemon(port=1111)

