from sqlalchemy import Column, DateTime, Integer, String, TEXT, ForeignKey, Float, Sequence
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    update_date = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        fields = ""
        for c in self.__table__.columns:
            if fields == "":
                fields = "{}='{}'".format(c.name, getattr(self, c.name))
            else:
                fields = "{}, {}='{}'".format(fields, c.name, getattr(self, c.name))
        return "<{}({})>".format(self.__class__.__name__, fields)

    @staticmethod
    def list_as_dict(items):
        return [i.as_dict() for i in items]

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Payment(BaseModel):
    __tablename__ = "payment"
    id = Column(Integer, Sequence('seq_reg_id', start=1, increment=1), primary_key=True)
    quantity = Column(Float)
    client_id = Column(Integer)


class PaymentReserve(BaseModel):

    __tablename__ = "payment_reserve"
    order_id = Column(Integer, primary_key=True)
    payment_id =Column(Integer, primary_key=True)
    reserved_quantity = Column(Float,nullable=False)
