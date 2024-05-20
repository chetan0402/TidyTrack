from sqlalchemy import Column, Integer, String

from database import Base


class Main(Base):
    __tablename__ = "main"
    ticketID = Column(Integer, primary_key=True, autoincrement=True)
    feedback = Column(String)
    imgpath = Column(String)
    rating = Column(Integer)
    locationcode = Column(String)
    time = Column(Integer)
    schno = Column(String)


class Tokens(Base):
    __tablename__ = "tokens"

    idtokens = Column(String, primary_key=True)
    time = Column(Integer)
    user = Column(String)


class Userbase(Base):
    __tablename__ = "userbase"

    name = Column(String(70))
    id = Column(String(12), primary_key=True, unique=True)
    phone = Column(Integer)
    usergroup = Column(Integer)


class OTP(Base):
    __tablename__ = "otp"

    id = Column(String, primary_key=True)
    tries = Column(Integer)
    otp = Column(Integer)
    firstTime = Column(Integer)
    deleteTime = Column(Integer)
    nextSendTime = Column(Integer)


class InternetComplain(Base):
    __tablename__ = "internet"

    ticket_id = Column(String, primary_key=True)
    location = Column(String)
    selected = Column(Integer)
    other = Column(String)
    img = Column(String)
    time = Column(Integer)
    user = Column(String)
