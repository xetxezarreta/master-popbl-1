from .saga_utils import State
from .event_publisher import Publisher
from .models import Order
from . import Session


class CreateOrderSaga():

    EVENT_OK = "OK"
    EVENT_FAIL = "FAIL"

    def __init__(self, order,reply_exchange,reply_topic):
        self.order = order
        self.state = None
        self.reply_exchange = reply_exchange
        self.reply_topic = reply_topic

    def start(self):
        self.state = ReserveDelivery(orchestrator=self)


# Saga state logic

class ReserveDelivery(State):

    def on_enter(self):
        pub = Publisher(reply_exchange=self.orchestrator.reply_exchange,
                        reply_topic=self.orchestrator.reply_topic)
        pub.delivery_reserve(self.orchestrator.order.id,
                             self.orchestrator.order.country)
        pub.close()

    def on_event(self, event):
        if event == self.orchestrator.EVENT_OK:
            self.orchestrator.state = ReserveMachine(self.orchestrator)
        elif event == self.orchestrator.EVENT_FAIL:
            self.orchestrator.state = SagaCancelled(self.orchestrator)


class ReserveMachine(State):

    def on_enter(self):
        pub = Publisher(reply_exchange=self.orchestrator.reply_exchange,
                        reply_topic=self.orchestrator.reply_topic)
        pub.machine_reserve(self.orchestrator.order.id,
                            self.orchestrator.order.number_of_pieces)
        pub.close()

    def on_event(self, event):
        if event == self.orchestrator.EVENT_OK:
            self.orchestrator.state = ReservePayment(self.orchestrator)
        elif event == self.orchestrator.EVENT_FAIL:
            self.orchestrator.state = CancelDelivery(self.orchestrator)


class ReservePayment(State):

    def on_enter(self):
        pub = Publisher(reply_exchange=self.orchestrator.reply_exchange,
                        reply_topic=self.orchestrator.reply_topic)
        PIECE_PRICE = 5
        pub.payment_reserve(client_id=self.orchestrator.order.client_id,
                            quantity=self.orchestrator.order.number_of_pieces*PIECE_PRICE, order_id=self.orchestrator.order.id)
        pub.close()

    def on_event(self, event):
        if event == self.orchestrator.EVENT_OK:
            self.orchestrator.state = PerformOrder(self.orchestrator)
        elif event == self.orchestrator.EVENT_FAIL:
            self.orchestrator.state = CancelMachine(self.orchestrator)


class CancelDelivery(State):

    def on_enter(self):
        pub = Publisher(reply_exchange=self.orchestrator.reply_exchange,
                        reply_topic=self.orchestrator.reply_topic)
        pub.delivery_cancel(self.orchestrator.order.id)
        pub.close()

        self.orchestrator.state = SagaCancelled(self.orchestrator)

    def on_event(self, event):
        pass


class CancelMachine(State):

    def on_enter(self):
        pub = Publisher(reply_exchange=self.orchestrator.reply_exchange,
                        reply_topic=self.orchestrator.reply_topic)
        pub.machine_cancel(self.orchestrator.order.id)
        pub.close()

        self.orchestrator.state = CancelDelivery(self.orchestrator)

    def on_event(self, event):
        pass


class PerformOrder(State):

    def on_enter(self):
        pub = Publisher(reply_exchange=self.orchestrator.reply_exchange,
                        reply_topic=self.orchestrator.reply_topic)
        pub.delivery_perform(self.orchestrator.order.id)
        pub.machine_perform(self.orchestrator.order.id)
        pub.payment_perform(self.orchestrator.order.id)
        pub.close()

        session = Session()
        order = session.query(Order).get(self.orchestrator.order.id)
        if not order:
            print("FATAL")
        else:
            order.status = Order.STATUS_ACCEPTED
            session.commit()

    def on_event(self, event):
        pass


class SagaCancelled(State):

    def on_enter(self):
        session = Session()
        order = session.query(Order).get(self.orchestrator.order.id)
        if not order:
            print("FATAL")
        else:
            order.status = Order.STATUS_CANCELLED
            session.commit()

        session.close()
