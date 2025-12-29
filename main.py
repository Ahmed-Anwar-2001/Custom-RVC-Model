import logging
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