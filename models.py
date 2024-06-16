from sqlalchemy import Column, Integer, String, Boolean

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
    role = Column(Integer)
    tries = Column(Integer)
    otp = Column(Integer)
    firstTime = Column(Integer)
    deleteTime = Column(Integer)
    nextSendTime = Column(Integer)


class Report(Base):
    __tablename__ = "report"

    ticket_id = Column(String(36), primary_key=True)
    location = Column(String)
    selected = Column(Integer)
    other = Column(String)
    img = Column(String)
    time = Column(Integer)
    user = Column(String)
    type = Column(Integer)


class SweeperRecords(Base):
    __tablename__ = "sweeperrecords"

    uuid = Column(String(36), primary_key=True)
    location = Column(String)
    img_path = Column(String)
    late = Column(Boolean)
    time = Column(Integer)
    sweeper = Column(String)
