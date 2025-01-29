from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base, engine  # Import Base and engine from database.py
import sys
print(sys.path)

from sqlalchemy import ForeignKey


# Drop and recreate all tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Database schema updated!")

# ✅ SQLAlchemy ORM Models (For Database)
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, nullable=False)  # Ensure file_path is defined
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    file_type = Column(String, nullable=True)  # Optional field for file type
    message_id = Column(Integer, nullable=True) # e.g., 'image' or 'video'

# ✅ Initialize the database schema
Base.metadata.create_all(bind=engine)
