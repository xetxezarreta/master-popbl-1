import json
from threading import Thread, Lock

import pika
import ssl
import logging
from os import environ
from .business_logic import BusinessLogic

logging.basicConfig()

rabbitmq_ip = environ.get("RABBITMQ_IP")
rabbitmq_port = environ.get("RABBITMQ_PORT")
rabbitmq_user = environ.get("RABBITMQ_USER")
rabbitmq_pass = environ.get("RABBITMQ_PASS")

ca_certs = environ.get("RABBITMQ_CA_CERT")
keyfile = environ.get("RABBITMQ_CLIENT_KEY")
certfile = environ.get("RABBITMQ_CLIENT_CERT")

ssl.match_hostname = lambda cert, hostname: True

class Handler(Thread):
    __stauslock__ = Lock()
    thread_session = None

    context = ssl.create_default_context(
        cafile=ca_certs)
    context.load_cert_chain(certfile,
                            keyfile)
    ssl_options = pika.SSLOptions(context, rabbitmq_ip)

    def __init__(self, exchange, binding_key, callback):
    
        Thread.__init__(self)
        self.exchange = exchange
        self.binding_key = binding_key
        self.queue_name = "logs_queue" 
        self.callback = callback
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)

        parameters = pika.ConnectionParameters(
            ssl_options=self.ssl_options,
            host=rabbitmq_ip, port=rabbitmq_port, virtual_host='/', credentials=credentials)

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self._init_queues()
        self.start()

    def _init_queues(self):
        self.channel.exchange_declare(exchange=self.exchange, exchange_type='topic')
        self.result = self.channel.queue_declare(queue=self.queue_name, exclusive=True)
        self.channel.queue_bind(exchange=self.exchange, queue=self.queue_name, routing_key=self.binding_key)

    def run(self):
        self.channel.basic_consume(queue=self.queue_name,
                                   auto_ack=True,
                                   on_message_callback=self.callback)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

    @staticmethod
    def print_callback(ch, method, properties, body):
        print(" [x] " + str(method.routing_key)+  " Received " + str(body))

    @staticmethod
    def log_callback(ch, method, properties, body):
        bl = BusinessLogic.getInstance()
        msg = json.loads(body)

        timestamp = msg["timestamp"]
        level = msg["level"]
        service_name = msg["service_name"]
        msg = msg["msg"]

        bl.add_log(timestamp,level,service_name,msg)
        print(" [x] " + str(method.routing_key)+  " Received " + str(body))
