from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.models import Message, Media
import aiofiles
import uuid
import os
from sqlalchemy import text
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import declarative_base
from datetime import datetime
from fastapi import HTTPException
from fastapi import UploadFile, File
from pydantic import BaseModel
from app.websocket_manager import manager


# ✅ Pydantic Models (For API Requests & Responses)
# Pydantic Models
from pydantic import BaseModel
from typing import List

# ✅ Pydantic Models (For API Requests & Responses)
class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    content: str

    class Config:
        from_attributes = True

class MessageUpdate(BaseModel):
    content: str

class FileUploadResponse(BaseModel):
    file_url: str

class DeleteResponse(BaseModel):
    message: str

class MediaResponse(BaseModel):
    id: int
    file_path: str

    class Config:
        from_attributes = True






@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup database and permissions
    with engine.connect() as connection:
        # Set necessary database permissions
        connection.execute(text('GRANT USAGE ON SCHEMA public TO chat_app_user;'))
        connection.execute(text('GRANT CREATE ON SCHEMA public TO chat_app_user;'))
        connection.execute(text('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chat_app_user;'))
        connection.execute(text('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO chat_app_user;'))
        connection.commit()

    # Create tables for Message and Media models
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

    yield  # Application runs here    
    

    
app = FastAPI(lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# Ensure the 'uploads' directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ✅ Mount Static Files
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def read_root():
    return {"message": "Welcome to the Chat Backend!"}


@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")


# ✅ WebSocket Message Handling (Store messages in DB)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = Message(content=data)
            db.add(message)
            db.commit()
            await manager.broadcast(data)
    except Exception as e:
        manager.disconnect(websocket)

# ✅ Create Message (POST)
@app.post("/messages/")
async def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    new_message = Message(content=message.content)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

# ✅ Get All Messages (GET)
@app.get("/messages/")
async def get_messages(db: Session = Depends(get_db)):
    return db.query(Message).all()

# ✅ Update Message (PUT)
@app.put("/messages/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: int, 
    message_update: MessageUpdate,  # ✅ Pydantic model ensures correct request body
    db: Session = Depends(get_db)
):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        return JSONResponse(status_code=404, content={"error": "Message not found"})
    
    message.content = message_update.content
    db.commit()
    db.refresh(message)
    return message

# ✅ Delete Message (DELETE)
@app.delete("/messages/{message_id}")
async def delete_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        return JSONResponse(status_code=404, content={"error": "Message not found"})
    db.delete(message)
    db.commit()
    return {"message": "Deleted successfully"}

# ✅ Upload File (POST)
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    db = next(get_db())  # Explicitly fetch session
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded.")

        if not file.content_type.startswith("image/"):  
            raise HTTPException(status_code=400, detail="Only image files are allowed.")

        file_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join("uploads", file_name)

        # os.makedirs("uploads", exist_ok=True)

        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        media = Media(file_path=file_path)
        db.add(media)
        db.commit()
        db.refresh(media)

        return {
            "file_url": f"/uploads/{file_name}",
            "file_name": file.filename,
            "content_type": file.content_type
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

    finally:
        db.close()  # Ensure session is closed


# ✅ Update Media (PUT)
@app.put("/media/{media_id}", response_model=MediaResponse)
async def update_media(media_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Replace the file
    file_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    # Update the database record
    media.file_path = file_path
    db.commit()
    db.refresh(media)
    return media

# ✅ Get All Uploaded Files (GET)
@app.get("/uploads/")
async def get_uploaded_files(db: Session = Depends(get_db)):
    try:
        files = db.query(Media).all()
        return [
            {
                "id": file.id,
                "file_path": file.file_path,
                "uploaded_at": file.uploaded_at,
            }
            for file in files
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving files: {str(e)}")

