from nimble.protocols import wsgi
from nimble.protocols import rabbitmq

class GEventServer(object):
    connection_protocol = wsgi

    def __init__(self, address, application, **opts):
        import gevent.wsgi
        self.server = gevent.wsgi.WSGIServer
        self.application = application
        self.address = address
        self.opts = opts

    def loop(self):
        #TODO:
        backlog = 256
        if 'backlog' in self.opts:
            backlog = self.opts['backlog']
            del self.opts['backlog']
        server = self.server(self.address, self.application, **self.opts)
        server.backlog = backlog
        server.serve_forever()

    def multicore_loop(self):
       import sys
       from gevent.socket import create_connection
       from gevent import wsgi
       from multiprocessing import Process, current_process, cpu_count

       listener = create_connection(self.address)

       def serve_forever(listener):
           self.server(listener, self.application, backlog=1024, **self.opts).serve_forever()

       number_of_processes = cpu_count()-1
       print 'Starting %s processes' % number_of_processes
       for i in range(number_of_processes):
           procs.append(Process(target=serve_forever, args=(listener,)))

       for p in procs:
           p.start()

       serve_forever(listener)
       for p in procs:
           p.join()

class FlupServer(object):
    connection_protocol = wsgi

    def __init__(self, address, application, **opts):
        import flup.server.fcgi
        self.server = flup.server.fcgi.WSGIServer
        self.application = application
        self.address = address
        self.opts = opts

    def loop(self):
        server = self.server(self.application, bindAddress=self.address, **self.opts)
        server.run()

class RabbitMQConsumer(object):
    connection_protocol = rabbitmq

    def __init__(self, address, application, **opts):
        from pika.adapters import SelectConnection

        self.address, _ = address
        self.application = application
        self.opts = opts

        self.adapter = SelectConnection
        self.connection = None
        self.channel = None

        self.queue = opts.pop('queue', None)
        if self.queue is None:
            raise TypeError('queue argument is required')

        try:
            self._init_send_mq()
        except socket.error as e:
            print "Can't connect to RabbitMQ: %s" % e
            #log.error("Can't connect to RabbitMQ: %s" % e)
            sys.exit(2)

    def _init_send_mq(self, queue=None):
        import pika
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.address))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue)    
        return (self.connection, self.channel)

    def loop(self):
        try:
            self._init_send_mq()
        except socket.error as e:
            print "Can't connect to RabbitMQ: %s" % e
            #log.error("Can't connect to RabbitMQ: %s" % e)
            sys.exit(2)

        def handle_delivery(channel, method_frame, header_frame, body):
            #print "Delivery", method_frame.delivery_tag
            environ = {
                'content-type': header_frame.content_type,
                'delivery-tag': method_frame.delivery_tag,
                'PATH_INFO': '',
                'body': body
            }
            self.application(environ, None)
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)


        self.channel.basic_consume(handle_delivery, queue=self.queue)
        self.channel.start_consuming()

    def async_loop(self):
        import pika

        def on_connected(connection):
            print "Connected to RabbitMQ"
            self.connection = connection
            connection.channel(on_channel_open)

        def on_channel_open(channel):
            print "Received RabbitMQ channel"
            self.channel = channel
            self.opts.setdefault('durable', True)
            self.opts.setdefault('auto_delete', False)
            self.opts.setdefault('exclusive', False)
            self.opts['callback'] = on_queue_declared
            channel.queue_declare(queue=self.queue, **self.opts)

        def on_queue_declared(frame):
            print self.queue, "Queue declared"
            self.channel.basic_consume(handle_delivery, queue=self.queue)

        def handle_delivery(channel, method_frame, header_frame, body):
            print "Delivery", method_frame.delivery_tag
            environ = {
                'content-type': header_frame.content_type,
                'delivery-tag': method_frame.delivery_tag,
                'PATH_INFO': '',
                'body': body
            }
            self.application(environ, None)
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)

        parameters = pika.ConnectionParameters(self.address)
        connection = self.adapter(parameters, on_connected)

        try:
            connection.ioloop.start()
        except KeyboardInterrupt:
            connection.close()
            connection.ioloop.start()

ALL = {
    'flup': FlupServer,
    'gevent': GEventServer,
    'rabbitmq': RabbitMQConsumer,
}

DEFAULT = GEventServer
