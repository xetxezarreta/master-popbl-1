from . import Session
from .models import Delivery
from .event_publisher import Publisher
import json

from .event_handler import Handler

class DeliveryLogic:
    __instance = None

    ORDER_EXCHANGE = "order_events"
    EVENT_OK = "OK"
    EVENT_FAIL = "FAIL"

    def __new__(cls):
        if DeliveryLogic.__instance is None:
            DeliveryLogic.__instance = object.__new__(cls)
        return DeliveryLogic.__instance

    def __init__(self):
            Handler(exchange=DeliveryLogic.ORDER_EXCHANGE, topic="order.delivery.*", callback= self.new_order_delivery_event,queue_name="order_delivery_events")


    def new_order_delivery_event(self, ch, method, properties, body):
        msg = json.loads(body)
        if "msgType" in msg and "orderId" in msg and "reply_exchange" in msg and "reply_topic" in msg:
            msgType = msg["msgType"]
            reply_exchange = msg["reply_exchange"]
            reply_topic = msg["reply_topic"]
        else: 
            print("msgType,reply and orderId are needed")
            return

        if msgType == "reserve":
            if "country" in msg:
                self.reserve_delivery(msg["country"], msg["orderId"],reply_exchange,reply_topic)
            else:
                "No country provided"
        if msgType == "cancel":
                self.cancel_delivery(msg["orderId"])
        if msgType == "perform":
                self.perform_delivery(msg["orderId"],reply_exchange,reply_topic)

        if msgType == "cancel_order":
            if "orderId" in msg:
                self.cancel_delivery(msg["orderId"])
                publisher = Publisher()
                publisher.send_order_cancelled_response(msg["orderId"],self.EVENT_OK,reply_exchange,reply_topic)
                publisher.close()



    def reserve_delivery(self, country, order_id,reply_exchange,reply_topic):
        session = Session()
        publisher = Publisher()
        # Check Country Logic
        if country == "araba" or country == "bizkaia" or country == "gipuzkoa":

            reserved_delivery = Delivery(
                order_id=order_id,
                status=Delivery.STATUS_RESERVED,
                description=country
            )
            session.add(reserved_delivery)
            session.commit()

            publisher.send_reserve_response(order_id, DeliveryLogic.EVENT_OK, reply_exchange,reply_topic)
            print("DeliveryLogic - Reserve Accepted - Accepted delivery zone")

        else:
            publisher.send_reserve_response(order_id, DeliveryLogic.EVENT_FAIL, reply_exchange,reply_topic)
            print("DeliveryLogic - Reserve Failed - Not accepted delivery zone")

        publisher.close()
        session.close()


    def perform_delivery(self, order_id,reply_exchange,reply_topic):

        session = Session()
        deliv = session.query(Delivery).filter_by(order_id=order_id, status=Delivery.STATUS_RESERVED).first()

        if deliv:
            deliv.status = Delivery.STATUS_CREATED
            session.commit()

            print("DeliveryLogic - Delivery Performed")
        else:
            print("FATAL Error in perform_delivery - no reserved delivery exits")

        session.close()


    def cancel_delivery(self, order_id):

        session = Session()
        deliv = session.query(Delivery).filter_by(order_id=order_id).first()
        
        if deliv:
            deliv.status = Delivery.STATUS_CANCELLED
            session.commit()
            print("DeliveryLogic - Delivery Canceled")
        else:
            print("FATAL Error in cancel_delivery -  no reserved delivery exits")

        session.close()
