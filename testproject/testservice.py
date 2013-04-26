#!/usr/bin/env python2.6

from nimble.server.base import Server
from nimble.client.base import ServerClient
from nimble.server.tools import shared, shared_as

from nimble.asyncjobs.base import AsyncJobManager

import time

class Database(object):
    def save(self, value):
        time.sleep(0.1)
        return True

class TestServer(Server):
    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)

        self.value = None

        try:
            self.db = AsyncJobManager(Database(), max_tasks=100, log_dir=self.log_dir)
        except Exception as e:
            self.log.debug(str(e))
            raise

    @shared
    def load(self, connection, value):
        value = int(value)
        self.value = value

        return connection.OK()

    @shared_as('add')
    def add(self, connection, valueToAdd):
        valueToAdd = int(valueToAdd)
        self.value += valueToAdd

        return connection.OK(str(self.value))

    @shared_as('div')
    def divide(self, connection, valueToDivide):
        valueToDivide = int(valueToDivide)
        self.value = int(self.value/valueToDivide)

        return connection.OK(str(self.value))

    @shared_as('save')
    def save_value(self, connection):
        self.db.save(self.value)

        return connection.OK()

    def shutdown(self):
        self.db.shutdown()

if __name__=='__main__':
    TestServer.run_daemon()

