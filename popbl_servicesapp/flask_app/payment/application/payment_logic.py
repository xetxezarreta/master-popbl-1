from . import Session
from .models import Payment, PaymentReserve
from .event_publisher import Publisher
from .event_handler import Handler
from sqlalchemy import func
import json


class PaymentLogic:

    __instance = None

    ORDER_EXCHANGE = "order_events"
    EVENT_OK = "OK"
    EVENT_FAIL = "FAIL"

    def __new__(cls):
        if PaymentLogic.__instance is None:
            PaymentLogic.__instance = object.__new__(cls)
        return PaymentLogic.__instance

    def __init__(self):
        Handler(exchange=PaymentLogic.ORDER_EXCHANGE, topic="order.payment.*",
                callback=self.new_order_payment_event, queue_name="order_payment_events")

    def new_order_payment_event(self, ch, method, properties, body):
        msg = json.loads(body)
        if "msgType" in msg and "orderId" in msg and "reply_exchange" in msg and "reply_topic" in msg:
            msgType = msg["msgType"]
            reply_exchange = msg["reply_exchange"]
            reply_topic = msg["reply_topic"]
            order_id = msg["orderId"]
        else:
            print("msgType,reply and orderId are needed")
            return

        if msgType == "reserve":
            if "quantity" in msg and "clientId" in msg:
                self.reserve_payment(
                    msg["quantity"], msg["clientId"], order_id, reply_exchange, reply_topic)
            else:
                print("No Quantity and/or clientid provided")
                return

        if msgType == "cancel":
            self.cancel_payment(order_id, reply_exchange, reply_topic)

        if msgType == "perform":
            self.perform_payment(order_id, reply_exchange, reply_topic)

        if msgType == "cancel_order":
            if "returnQuantity" in msg and "clientId" in msg:
                self.return_money(msg["clientId"], msg["returnQuantity"])
                publisher = Publisher()
                publisher.send_order_cancelled_response(order_id,self.EVENT_OK,reply_exchange,reply_topic)
                publisher.close()
                
                

    def add_payment(self, quantity, client):
        session = Session()
        query = session.query(Payment).filter_by(client_id=client)

        if query.count() == 0:
            p = Payment(
                quantity=quantity,
                client_id=client
            )
            session.add(p)
        else:
            p = query.first()
            p.quantity = p.quantity + quantity

        session.commit()

   
    def get_client_payment(self, client_id):
        session = Session()
        query = session.query(Payment).filter_by(client_id=client_id)
        if query.count() == 0:
            return "Client not found"
        else:
            payment = query.first()
            return "Client {} has {}$" .format(payment.client_id,payment.quantity)




   
    def reserve_payment(self, quantity, client, order_id, reply_exchange, reply_topic):
        session = Session()
        query = session.query(Payment).filter_by(client_id=client)

        publisher = Publisher()

        if query.count() == 0:
            # Not payment entry for the client
            publisher.send_reserve_response(
                order_id, PaymentLogic.EVENT_FAIL, reply_exchange, reply_topic)
            print("BusinnessLogic -  Reserve Failed - Not payment entry for the client")
        else:
            p = query.first()
            sum_query = session.query(PaymentReserve, func.sum(PaymentReserve.reserved_quantity)).filter_by(
                payment_id=p.id).group_by(PaymentReserve.reserved_quantity)

            if sum_query.count() != 0:
                reserved_quantity = sum_query.first()[1]            
            else:
                reserved_quantity = 0

            if (p.quantity - reserved_quantity) < quantity:
                # Not enough money
                publisher.send_reserve_response(
                    order_id, PaymentLogic.EVENT_FAIL, reply_exchange, reply_topic)
                print("BusinnessLogic -  Reserve Failed - Not enough money")
            else:
                # Reserve the money
                pr = PaymentReserve(
                    order_id=order_id, payment_id=p.id, reserved_quantity=quantity)
                session.add(pr)
                session.commit()
                publisher.send_reserve_response(
                    order_id, PaymentLogic.EVENT_OK, reply_exchange, reply_topic)
                print("BusinnessLogic -  Reserve Done")

        session.close()
        publisher.close()

    def perform_payment(self, order_id, reply_exchange, reply_topic):
        session = Session()
        reserve = session.query(PaymentReserve).filter_by(
            order_id=order_id).first()
        if reserve:
            payment = session.query(Payment).filter_by(
                id=reserve.payment_id).first()
            if payment:
                payment.quantity -= reserve.reserved_quantity
                session.delete(reserve)
                session.commit()
                print("BusinnessLogic -  Payment Performed")
            else:
                print(" FATAL ERROR : No payment exists")
        else:
            print("FATAL ERROR : No reserverd quantity")
        
        session.close()



    def cancel_payment(self, order_id, reply_exchange, reply_topic):
        session = Session()
        reserve = session.query(PaymentReserve).filter_by(
            order_id=order_id).first()
        if reserve:
            session.delete(reserve)
            session.commit()
            print("BusinnessLogic -  Payment Canceled")
        else:
            print("FATAL ERROR : No reserverd Quantity")

        session.close()

    def return_money(self, client_id, return_quantity):
        session = Session()
        query = session.query(Payment).filter_by(client_id=client_id)

        if query.count() == 0:
            print ("FATAL")
            exit(1)

        publisher = Publisher()

        payment = query.first()
        payment.quantity += return_quantity
        session.commit()
        session.close()

        publisher.send_log("{}$ was refounded".format(return_quantity))

        
