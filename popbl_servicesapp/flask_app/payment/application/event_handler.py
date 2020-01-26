import json
from threading import Thread, Lock

import pika
import ssl
import logging
from os import environ
from .config import Config


logging.basicConfig()

config = Config.get_instance()

ssl.match_hostname = lambda cert, hostname: True

class Handler(Thread):
    __stauslock__ = Lock()
    thread_session = None

    context = ssl.create_default_context(
        cafile=config.CA_CERTS)
    context.load_cert_chain(config.CERTFILE,
                            config.KEYFILE)
    ssl_options = pika.SSLOptions(context, config.RABBITMQ_IP)

    def __init__(self, exchange, topic, callback, queue_name):
        Thread.__init__(self)
        self.exchange = exchange
        self.binding_key = topic
        self.queue_name = queue_name
        self.callback = callback
        credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASS)

        parameters = pika.ConnectionParameters(
            ssl_options=self.ssl_options,
            host=config.RABBITMQ_IP, port=config.RABBITMQ_PORT, virtual_host='/', credentials=credentials)

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self._init_queues()
        self.start()

    def _init_queues(self):
        self.channel.exchange_declare(
            exchange=self.exchange, exchange_type='topic')
        self.result = self.channel.queue_declare(
            queue=self.queue_name, exclusive=True)
        self.channel.queue_bind(
            exchange=self.exchange, queue=self.queue_name, routing_key=self.binding_key)

    def run(self):
        self.channel.basic_consume(queue=self.queue_name,
                                   auto_ack=True,
                                   on_message_callback=self.callback)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        # Publisher.test()
        self.channel.start_consuming()


    