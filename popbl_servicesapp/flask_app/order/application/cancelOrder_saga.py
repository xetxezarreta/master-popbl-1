from .saga_utils import State
from .event_publisher import Publisher
from .models import Order,Piece
from . import Session


class CancelOrderSaga():

    EVENT_OK = "OK"
    EVENT_FAIL = "FAIL"

    def __init__(self, order, reply_exchange, reply_topic):
        self.order = order
        self.state = None
        self.reply_exchange = reply_exchange
        self.reply_topic = reply_topic

    def start(self):
        self.state = CancelMachine(orchestrator=self)


# Saga state logic

class CancelMachine(State):

    def on_enter(self):
        pub = Publisher(reply_exchange=self.orchestrator.reply_exchange,
                        reply_topic=self.orchestrator.reply_topic)
        pub.machine_order_cancelled(self.orchestrator.order.id)
        pub.close()

    def on_event(self, event):
        if event == self.orchestrator.EVENT_OK:
            self.orchestrator.state = CancelDelivery(self.orchestrator)
        elif event == self.orchestrator.EVENT_FAIL:
            print("FATAL SAGA FAILED")
            exit(1)


class CancelDelivery(State):

    def on_enter(self):
        pub = Publisher(reply_exchange=self.orchestrator.reply_exchange,
                        reply_topic=self.orchestrator.reply_topic)
        pub.delivery_order_cancelled(self.orchestrator.order.id)
        pub.close()

    def on_event(self, event):
        if event == self.orchestrator.EVENT_OK:
            self.orchestrator.state = CancelPayment(self.orchestrator)
        elif event == self.orchestrator.EVENT_FAIL:
            print("FATAL SAGA FAILED")
            exit(1)


class CancelPayment(State):

    def on_enter(self):
        pub = Publisher(reply_exchange=self.orchestrator.reply_exchange,
                        reply_topic=self.orchestrator.reply_topic)

        return_quantity = 5 * len(self.orchestrator.order.pieces)
        pub.payment_order_cancelled(self.orchestrator.order.id, self.orchestrator.order.client_id,return_quantity)
        pub.close()

    def on_event(self, event):
        if event == self.orchestrator.EVENT_OK:
            self.orchestrator.state = SagaFinished(self.orchestrator)
        elif event == self.orchestrator.EVENT_FAIL:
            print("FATAL SAGA FAILED")
            exit(1)


class SagaFinished(State):

    def on_enter(self):
        session = Session()
        order = session.query(Order).get(self.orchestrator.order.id)

        if not order:
            print("FATAL")
            session.close()
            exit(1)
        else:
            order.status = Order.STATUS_CANCELLED
            for p in order.pieces:
                p.status = Piece.STATUS_CANCELLED
            session.commit()
            session.close()


    def on_event(self):
        pass
