import logging
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from engine import engine

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    engine.initialize()

# --- NEW STABLE HTTP ENDPOINT ---
@app.post("/convert")
async def convert_audio_http(file: UploadFile = File(...)):
    """Stable HTTP endpoint for RVC conversion"""
    try:
        # Read the uploaded audio bytes
        input_bytes = await file.read()
        
        # Process via RVC Engine
        output_bytes = await engine.process_audio_bytes(input_bytes)
        
        # Return as audio/wav
        return Response(content=output_bytes, media_type="audio/wav")
    except Exception as e:
        logger.error(f"HTTP Processing Error: {e}")
        return Response(content=str(e), status_code=500)

@app.websocket("/ws/convert")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client Connected")
    
    try:
        while True:
            # 1. Receive Audio Blob (Bytes) from Client
            input_audio = await websocket.receive_bytes()
            
            if not input_audio:
                continue

            # 2. Process via RVC
            # This handles saving to file, GPU processing, and reading back
            output_audio = await engine.process_audio_bytes(input_audio)
            
            # 3. Send Converted Audio Back
            await websocket.send_bytes(output_audio)
            
    except WebSocketDisconnect:
        logger.info("Client Disconnected")
    except Exception as e:
        logger.error(f"Processing Error: {e}")
        # Optional: Send text error to client if needed
        # await websocket.send_text("Error processing audio")