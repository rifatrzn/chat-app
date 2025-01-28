from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

# URL encode the password properly
DATABASE_URL = "postgresql://chat_app_user:admin123@db:5432/chat_app_db"

# Create engine with proper error handling
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800
    )
    print("Successfully connected to the database!")
except OperationalError as e:
    print(f"Could not connect to database. Error: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Add this function
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
