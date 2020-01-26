import json
import pika
import logging

import ssl
from datetime import datetime
from .config import Config


logging.basicConfig()

config = Config.get_instance()

ORDER_EXCHANGE = "order_events"


ssl.match_hostname = lambda cert, hostname: True


class Publisher(object):

    def __init__(self, reply_exchange=None, reply_topic=None):
        self.create_connection()
        self.reply_exchange = reply_exchange
        self.reply_topic = reply_topic

    def create_connection(self):
        context = ssl.create_default_context(
            cafile=config.CA_CERTS)
        context.load_cert_chain(config.CERTFILE,
                                config.KEYFILE)
        ssl_options = pika.SSLOptions(context, config.RABBITMQ_IP)

        credentials = pika.PlainCredentials(
            config.RABBITMQ_USER, config.RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            ssl_options=ssl_options,
            host=config.RABBITMQ_IP, port=config.RABBITMQ_PORT, virtual_host='/', credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.exchange_declare(
            exchange=ORDER_EXCHANGE, exchange_type='topic')
        channel.exchange_declare(exchange="LogExchange", exchange_type='topic')
        self.connection = connection
        self.channel = channel

    def close(self):
        self.connection.close()

    ## PAYMENT #############################################################
    def payment_reserve(self, client_id, quantity, order_id):
        body = {"clientId": client_id,
                "quantity": quantity, "orderId": order_id, "msgType": "reserve"}

        if self.reply_exchange and self.reply_topic:
            body["reply_exchange"] = self.reply_exchange
            body["reply_topic"] = self.reply_topic

        binding_key = 'order.payment.reserve'

        self.channel.basic_publish(exchange=ORDER_EXCHANGE,
                                   routing_key=binding_key,
                                   body=json.dumps(body))

        self.send_log("Payment Reserve: " + str(body))

        print(" [x] Sent " + str(body) + "to " + binding_key + " topic")

    def payment_perform(self, order_id):
        body = {"orderId": order_id, "msgType": "perform"}
        binding_key = 'order.payment.perform'

        if self.reply_exchange and self.reply_topic:
            body["reply_exchange"] = self.reply_exchange
            body["reply_topic"] = self.reply_topic

        self.channel.basic_publish(exchange=ORDER_EXCHANGE,
                                   routing_key=binding_key,
                                   body=json.dumps(body))

        self.send_log("Payment Perform : " + str(body))

        print(" [x] Sent " + str(body) + "to " + binding_key + " topic")

    def payment_cancel(self, order_id):
        body = {"orderId": order_id, "msgType": "cancel"}
        binding_key = 'order.payment.cancel'

        if self.reply_exchange and self.reply_topic:
            body["reply_exchange"] = self.reply_exchange
            body["reply_topic"] = self.reply_topic

        self.channel.basic_publish(exchange=ORDER_EXCHANGE,
                                   routing_key=binding_key,
                                   body=json.dumps(body))

        self.send_log("Payment Cancel: " + str(body))

        print(" [x] Sent " + str(body) + "to " + binding_key + " topic")

    def payment_order_cancelled(self, order_id, client_id, return_quantity):
        body = {"orderId": order_id, "clientId": client_id, "msgType": "cancel_order", "returnQuantity": return_quantity}

        if self.reply_exchange and self.reply_topic:
            body["reply_exchange"] = self.reply_exchange
            body["reply_topic"] = self.reply_topic

        binding_key = 'order.payment.cancel_order'

        self.channel.basic_publish(exchange=ORDER_EXCHANGE,
                                   routing_key=binding_key,
                                   body=json.dumps(body))

        self.send_log("Sent Cancel Order to Payment: " + str(body))

        print(" [x] Sent " + str(body) + "to " + binding_key + " topic")

    ## DELIVERY #############################################################

    def delivery_reserve(self, order_id, country):
        body = {"orderId": order_id, "country": country, "msgType": "reserve"}
        binding_key = 'order.delivery.reserve'

        if self.reply_exchange and self.reply_topic:
            body["reply_exchange"] = self.reply_exchange
            body["reply_topic"] = self.reply_topic

        self.channel.basic_publish(exchange=ORDER_EXCHANGE,
                                   routing_key=binding_key,
                                   body=json.dumps(body))
        self.send_log("Delivery Reserve: " + str(body))
        print(" [x] Sent " + str(body) + "to " + binding_key + " topic")

    def delivery_perform(self, order_id):
        body = {"orderId": order_id, "msgType": "perform"}
        binding_key = 'order.delivery.perform'

        if self.reply_exchange and self.reply_topic:
            body["reply_exchange"] = self.reply_exchange
            body["reply_topic"] = self.reply_topic

        self.channel.basic_publish(exchange=ORDER_EXCHANGE,
                                   routing_key=binding_key,
                                   body=json.dumps(body))
        self.send_log("Delivery Perform: " + str(body))
        print(" [x] Sent " + str(body) + "to " + binding_key + " topic")

    def delivery_cancel(self, order_id):
        body = {"orderId": order_id, "msgType": "cancel"}
        binding_key = 'order.delivery.cancel'

        if self.reply_exchange and self.reply_topic:
            body["reply_exchange"] = self.reply_exchange
            body["reply_topic"] = self.reply_topic

        self.channel.basic_publish(exchange=ORDER_EXCHANGE,
                                   routing_key=binding_key,
                                   body=json.dumps(body))
        self.send_log("Delivery Cancel: " + str(body))
        print(" [x] Sent " + str(body) + "to " + binding_key + " topic")

    def delivery_order_cancelled(self, order_id):
        body = {"orderId": order_id, "msgType": "cancel_order"}

        if self.reply_exchange and self.reply_topic:
            body["reply_exchange"] = self.reply_exchange
            body["reply_topic"] = self.reply_topic

        binding_key = 'order.delivery.cancel_order'

        self.channel.basic_publish(exchange=ORDER_EXCHANGE,
                                   routing_key=binding_key,
                                   body=json.dumps(body))

        self.send_log("Sent Cancel Order to Delivery: " + str(body))

        print(" [x] Sent " + str(body) + "to " + binding_key + " topic")


    ## MACHINE #############################################################

    def machine_reserve(self, order_id, number_of_pieces):

        body = {"orderId": order_id,
                "numberOfPieces": number_of_pieces, "msgType": "reserve"}
        binding_key = 'order.machine.reserve'

        if self.reply_exchange and self.reply_topic:
            body["reply_exchange"] = self.reply_exchange
            body["reply_topic"] = self.reply_topic

        self.channel.basic_publish(exchange=ORDER_EXCHANGE,
                                   routing_key=binding_key,
                                   body=json.dumps(body))

        self.send_log("Machine Reserve: " + str(body))

        print(" [x] Sent " + str(body) + "to " + binding_key + " topic")

    def machine_perform(self, order_id, description="default description"):

        body = {"orderId": order_id,
                "description": description, "msgType": "perform"}
        binding_key = 'order.machine.perform'

        if self.reply_exchange and self.reply_topic:
            body["reply_exchange"] = self.reply_exchange
            body["reply_topic"] = self.reply_topic

        self.channel.basic_publish(exchange=ORDER_EXCHANGE,
                                   routing_key=binding_key,
                                   body=json.dumps(body))

        self.send_log("Machine Perform: " + str(body))
        print(" [x] Sent " + str(body) + "to " + binding_key + " topic")

    def machine_cancel(self, order_id):

        body = {"orderId": order_id, "msgType": "cancel"}
        binding_key = 'order.machine.cancel'

        if self.reply_exchange and self.reply_topic:
            body["reply_exchange"] = self.reply_exchange
            body["reply_topic"] = self.reply_topic

        self.channel.basic_publish(exchange=ORDER_EXCHANGE,
                                   routing_key=binding_key,
                                   body=json.dumps(body))

        self.send_log("Machine Cancel: " + str(body))
        print(" [x] Sent " + str(body) + "to " + binding_key + " topic")

    def machine_order_cancelled(self, order_id):
        body = {"orderId": order_id, "msgType": "cancel_order"}

        if self.reply_exchange and self.reply_topic:
            body["reply_exchange"] = self.reply_exchange
            body["reply_topic"] = self.reply_topic

        binding_key = 'order.machine.cancel_order'

        self.channel.basic_publish(exchange=ORDER_EXCHANGE,
                                   routing_key=binding_key,
                                   body=json.dumps(body))

        self.send_log("Sent Cancel Order to Machine: " + str(body))

        print(" [x] Sent " + str(body) + "to " + binding_key + " topic")


    ## LOGGER

    def send_log(self, msg):

        log_msg = dict()
        log_msg["timestamp"] = str(datetime.now())
        log_msg["level"] = "INFO"
        log_msg["service_name"] = "Order"
        log_msg["msg"] = msg

        self.channel.basic_publish(exchange="LogExchange",
                                   routing_key="INFO",
                                   body=json.dumps(log_msg))
