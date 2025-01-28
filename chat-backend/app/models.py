from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer)
    receiver_id = Column(Integer)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    file_url = Column(String)
    file_type = Column(String)  # e.g., 'image' or 'video'
