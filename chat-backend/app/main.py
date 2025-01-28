from fastapi import FastAPI, WebSocket, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from app.websocket_manager import manager
from app.database import Base, engine, get_db
from app.models import Message, Media
import aiofiles
import uuid
import os
from sqlalchemy import text
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup - runs before application starts
    with engine.connect() as connection:
        # Grant necessary permissions
        connection.execute(text('GRANT USAGE ON SCHEMA public TO chat_app_user;'))
        connection.execute(text('GRANT CREATE ON SCHEMA public TO chat_app_user;'))
        connection.execute(text('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chat_app_user;'))
        connection.execute(text('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO chat_app_user;'))
        connection.commit()
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield  # Application runs here
    
    # Cleanup - runs when application is shutting down
    # Add any cleanup code here if needed

app = FastAPI(lifespan=lifespan)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except Exception as e:
        manager.disconnect(websocket)

@app.post("/upload/")
async def upload_file(file: UploadFile):
    file_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"uploads/{file_name}"
    
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    return {"file_url": f"/uploads/{file_name}"}
