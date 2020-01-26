from . import Session
from sqlalchemy import func

from .models import Piece, Order, MachineReserve
from .event_publisher import Publisher
from .machine import Machine

from .event_handler import Handler
import json

MAX_PIECES_IN_QUEUE = 5

class MachineLogic:
    
    __instance = None

    ORDER_EXCHANGE = "order_events"
    EVENT_OK = "OK"
    EVENT_FAIL = "FAIL"



    def __new__(cls):
        if MachineLogic.__instance is None:
            MachineLogic.__instance = object.__new__(cls)
        return MachineLogic.__instance

    def __init__(self):
        Handler(exchange=MachineLogic.ORDER_EXCHANGE, topic="order.machine.*",
                callback=self.new_order_machine_event, queue_name="order_machine_events")
        self.my_machine = Machine(machine_logic=self)

    def new_order_machine_event(self, ch, method, properties, body):
        
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
            if "numberOfPieces" in msg:
                self.reserve_machine(order_id, msg["numberOfPieces"], reply_exchange, reply_topic)
        if msgType == "cancel":
            self.cancel_machine(order_id, reply_exchange, reply_topic)
        if msgType == "perform":
            self.perform_machine(order_id, reply_exchange, reply_topic)
        if msgType == "cancel_order":
            self.cancel_order_machine(order_id, reply_exchange, reply_topic)

    def reserve_machine(self,order_id, npieces,  reply_exchange, reply_topic):
        session = Session()

        # Check free spaces
        query = session.query(MachineReserve, func.sum(
            MachineReserve.reserved_spaces)).group_by(MachineReserve.reserved_spaces)

        if query.count() != 0:
            reserved_spaces = query.first()[1]
        else:
            reserved_spaces = 0

        queued_spaces = len(session.query(Piece).filter_by(
            status=Piece.STATUS_QUEUED).all())

        publisher = Publisher()

        if reserved_spaces + queued_spaces >= MAX_PIECES_IN_QUEUE:
            # No free space
            publisher.send_reserve_response(
                order_id, MachineLogic.EVENT_FAIL, reply_exchange, reply_topic)
            print(
                "MachineLogic -  Machine Failed - Cannot queued more than {} pieces per order".format(MAX_PIECES_IN_QUEUE))
        else:
            # Create Machine Reserve
            o = MachineReserve(order_id=order_id, reserved_spaces=npieces)
            session.add(o)
            session.commit()

            publisher.send_reserve_response(
                order_id, MachineLogic.EVENT_OK, reply_exchange, reply_topic)
            print(
                "MachineLogic - Machine has reserved {} pieces for order id: {}".format(npieces, order_id))

        publisher.close()
        session.close()

    def perform_machine(self, order_id, reply_exchange, reply_topic):
        session = Session()

        machine_reserve = session.query(
            MachineReserve).filter_by(order_id=order_id)
        if machine_reserve.count() == 0:
            print(
                " FATAL MachineLogic -  Machine Failed - There is not any reserve for that order_id")

        else:
            new_order = Order(id=order_id,
                              number_of_pieces=machine_reserve.first().reserved_spaces,
                              description="",
                              status=Order.STATUS_ACCEPTED)
            session.add(new_order)

            for i in range(new_order.number_of_pieces):
                piece = Piece(status=Piece.STATUS_QUEUED,
                              order_id=order_id)

                piece.order = new_order
                session.add(piece)

            # Remove Reserve
            session.delete(machine_reserve.first())
            session.commit()

            # Add Pieces
            self.my_machine.add_pieces_to_queue(new_order.pieces)

        session.close()

    def cancel_machine(self, order_id, reply_exchange, reply_topic):
        session = Session()

        machine_reserve = session.query(
            MachineReserve).filter_by(order_id=order_id).first()

        if not machine_reserve:
            print(
                " FATAL MachineLogic -  Machine Failed - There is not any reserve for that order_id")

        session.delete(machine_reserve)
        session.commit()
        print("MachineLogic - Machine cancel - Success")

        session.close()

        return True

    def cancel_order_machine(self, order_id, reply_exchange, reply_topic):
        self.my_machine.remove_pieces_from_queue(order_id)
        publisher = Publisher()
        publisher.send_cancel_order_response(order_id, MachineLogic.EVENT_OK, reply_exchange, reply_topic)
        publisher.close()





    def piece_finished(self, piece):
        order_finished = True
        for piece in piece.order.pieces:
            if piece.status != Piece.STATUS_MANUFACTURED:
                order_finished = False
        if order_finished:
            print("ORDER " + str(piece.order.id) + " FINISHED")
            piece.order.status = Order.STATUS_FINISHED
            publisher = Publisher()
            publisher.publish_order_finished(piece.order.id)
            publisher.close()
        
        
    
    def get_status(self):
        working_piece = self.my_machine.working_piece
        queue = self.my_machine.queue
        if working_piece:
            working_piece = working_piece.as_dict()
        response = {"status": self.my_machine.status,
                    "working_piece": working_piece, "queue": list(queue)}
        return response
