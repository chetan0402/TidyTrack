from sqlalchemy import Column, Integer, String, Boolean, PrimaryKeyConstraint

from database import Base


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
    rating = Column(Integer)
    status = Column(Integer)


class SweeperRecords(Base):
    __tablename__ = "sweeperrecords"

    uuid = Column(String(36), primary_key=True)
    location = Column(String)
    img_path = Column(String)
    late = Column(Boolean)
    time = Column(Integer)
    sweeper = Column(String)


class UserbaseAttr(Base):
    __tablename__ = "userbaseAttr"

    id = Column(String(12), primary_key=True)
    subgroup = Column(Integer)


class ReportPara(Base):
    __tablename__ = "reportPara"

    report_id = Column(String(36), primary_key=True)
    from_time = Column(Integer)
    to_time = Column(Integer)
    location = Column(String)
    report_type = Column(Integer)
    expiry = Column(Integer)


class SweeperAssign(Base):
    __tablename__ = "sweeperAssign"

    sweeper = Column(String(12), primary_key=True)
    location = Column(String, primary_key=True)

    __table_args__ = (
        PrimaryKeyConstraint('sweeper', 'location'),
    )
