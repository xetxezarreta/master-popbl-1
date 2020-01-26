from sqlalchemy import Column, DateTime, Integer, String, TEXT, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    update_date = Column(DateTime, nullable=False,
                         server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        fields = ""
        for c in self.__table__.columns:
            if fields == "":
                fields = "{}='{}'".format(c.name, getattr(self, c.name))
            else:
                fields = "{}, {}='{}'".format(
                    fields, c.name, getattr(self, c.name))
        return "<{}({})>".format(self.__class__.__name__, fields)

    @staticmethod
    def list_as_dict(items):
        return [i.as_dict() for i in items]

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class User(BaseModel):
    ROL_CLIENT = "client"
    ROL_ADMIN = "admin"

    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(TEXT, nullable=False)
    password = Column(TEXT, nullable=False)
    rol = Column(TEXT,  nullable=False) 
    permissions = relationship("Permission", lazy="joined", cascade='all, delete-orphan')

    def as_dict(self):
        d = super().as_dict()
        return d


class Permission(BaseModel):

    C_OWN_ORDER = "C OWN ORDER"
    R_OWN_ORDER = "R OWN ORDER"
    U_OWN_ORDER = "U OWN ORDER"
    D_OWN_ORDER = "D OWN ORDER"
    C_ALL = "C ALL ALL"
    R_ALL = "R ALL ALL"
    U_ALL = "U ALL ALL"
    D_ALL = "D ALL ALL"

    __tablename__ = "permission"
    rol = Column(TEXT, ForeignKey('user.rol'), primary_key=True )
    permission = Column(TEXT, primary_key=True)
