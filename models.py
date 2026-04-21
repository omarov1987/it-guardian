from sqlalchemy import Column, String, Integer, DateTime, Boolean
from datetime import datetime
from database import Base


class Device(Base):
    __tablename__ = "devices"

    hostname = Column(String, primary_key=True, index=True)

   
   # owner_id = Column(Integer)

    os = Column(String)
    disk_free = Column(Integer)
    last_seen = Column(DateTime, default=datetime.utcnow)

    # alert flags
    offline_alert_sent = Column(Boolean, default=False)
    disk_alert_sent = Column(Boolean, default=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)