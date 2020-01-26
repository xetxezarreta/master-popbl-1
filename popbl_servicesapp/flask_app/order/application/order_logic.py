from . import Session
from .models import Order, Piece
from . import Session
from .saga_utils import SagaManager
from .createOrder_saga import CreateOrderSaga
from .cancelOrder_saga import CancelOrderSaga
from .event_handler import Handler
from .event_publisher import Publisher
import json


class OrderLogic():

    __instance = None
    SAGAS_REPLY_EXCHANGE = "sagas_replies"
    ALL_SAGA_REPLIES_TOPIC = "replies.*"
    CREATE_ORDER_SAGA_REPLY_TOPIC = "replies.createOrderSaga"
    CANCEL_ORDER_SAGA_REPLY_TOPIC = "replies.cancelOrderSaga"

    def __new__(cls):
        if OrderLogic.__instance is None:
            OrderLogic.__instance = object.__new__(cls)
        return OrderLogic.__instance

    def __init__(self):
        self.mng_CreateOrder = SagaManager()
        self.mng_CancelOrder = SagaManager()
        Handler(exchange=OrderLogic.SAGAS_REPLY_EXCHANGE, topic=OrderLogic.ALL_SAGA_REPLIES_TOPIC,
                callback=self.saga_replies_msg_recived, queue_name="saga_replies_queue")
        Handler(exchange="machine_events", topic="machine.finished_orders",
                callback=self.machine_event_order_finished, queue_name="machine_order_finished_orders")

    # Mesasage recived on the create order_saga reply queue

    def saga_replies_msg_recived(self, ch, method, properties, body):

        if method.routing_key == self.CREATE_ORDER_SAGA_REPLY_TOPIC:
            msg = json.loads(body)

            if "orderId" in msg and "response" in msg:
                print("order{}, response {}".format(msg["orderId"], msg["response"]))
                saga = self.mng_CreateOrder.get_saga(int(msg["orderId"]))
                saga.state.on_event(msg["response"])
            else:
                print("Invalid data")

            return


        if method.routing_key == self.CANCEL_ORDER_SAGA_REPLY_TOPIC:          
            msg = json.loads(body)

            if "orderId" in msg and "response" in msg:
                print("order{}, response {}".format(msg["orderId"], msg["response"]))
                saga = self.mng_CancelOrder.get_saga(int(msg["orderId"]))
                saga.state.on_event(msg["response"])
            else:
                print("Invalid data")
            
            return


        print("Invalid msg in saga replies queue")



    def machine_event_order_finished(self, ch, method, properies, body):
        msg = json.loads(body)
        if "orderId" in msg:
            session = Session()
            order = session.query(Order).get(msg["orderId"])
            if not order:
                print("FATAL: order dosen't exists")
                session.close()
                return

            if order.status == Order.STATUS_CANCELLED:
                session.close()
                return

            order.status = Order.STATUS_FINISHED
            publisher = Publisher()
            publisher.send_log("Order {} finshed recived ".format(order.id))

            publisher.close()
            session.commit()
            session.close()

    def create_order(self, description, country, number_of_pieces, client_id):
        session = Session()
        new_order = None
        new_order = Order(
            description=description,
            country=country,
            number_of_pieces=number_of_pieces,
            client_id=client_id,
            status=Order.STATUS_PENDING
        )
        session.add(new_order)
        for i in range(new_order.number_of_pieces):
            piece = Piece()
            piece.status = Piece.STATUS_CREATED
            piece.order = new_order
            session.add(piece)

        session.commit()

        new_saga = CreateOrderSaga(
            new_order, OrderLogic.SAGAS_REPLY_EXCHANGE, OrderLogic.CREATE_ORDER_SAGA_REPLY_TOPIC)
        self.mng_CreateOrder.add(new_order.id, new_saga)
        self.mng_CreateOrder.start(new_order.id)

        order_id = new_order.id
        session.close()

        return order_id

    def cancel_order(self, order_id):
        session = Session()
        order = session.query(Order).get(order_id)

        if not order:
            return "Order dosen't exists"

        if order.status == Order.STATUS_PENDING:
            return "Your order is still on our servers please try later"

        if order.status == Order.STATUS_CANCELLED:
            return "Your order creation process failed and the order was cancelled"

        if order.status == Order.STATUS_FINISHED:
            return "Sorry your order was completed and delivered"

        if order.status == Order.STATUS_ACCEPTED:
            new_saga = CancelOrderSaga(order, OrderLogic.SAGAS_REPLY_EXCHANGE, OrderLogic.CANCEL_ORDER_SAGA_REPLY_TOPIC)
            self.mng_CancelOrder.add(order.id, new_saga)
            self.mng_CancelOrder.start(order.id)
            return "The order {} was cancelled successfully".format(order.id)

        session.close()

    def get_order(self, order_id):
        session = Session()
        order = session.query(Order).get(order_id)
        if not order:
            session.close()
            return None
        print("GET Order {}: {}".format(order_id, order))
        session.close()
        return order.as_dict()

    def get_all_orders(self):
        print("GET All Orders.")
        session = Session()
        orders = session.query(Order).all()
        session.close()
        return Order.list_as_dict(orders)
