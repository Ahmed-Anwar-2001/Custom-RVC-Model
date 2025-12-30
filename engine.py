import os
import logging
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from rvc_python.infer import RVCInference
from config import settings

logger = logging.getLogger("rvc_engine")

class RVCEngine:
    _instance = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self.rvc = None
        self.executor = ThreadPoolExecutor(max_workers=1) # Prevent GPU OOM

    def initialize(self):
        """Load Model into VRAM"""
        logger.info(f"Loading RVC Model on {settings.DEVICE}...")
        
        self.rvc = RVCInference(device=settings.DEVICE)
        
        model_path = os.path.join(settings.MODEL_DIR, f"{settings.MODEL_NAME}.pth")
        index_path = os.path.join(settings.MODEL_DIR, f"{settings.MODEL_NAME}.index")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file missing: {model_path}")
            
        self.rvc.load_model(model_path)
        
        if os.path.exists(index_path):
            self.rvc.set_index(index_path)
            logger.info("Index file loaded.")
        
        logger.info("RVC Engine Ready.")

    async def process_audio_bytes(self, audio_bytes: bytes) -> bytes:
        """
        1. Save input bytes to RAM disk
        2. Run RVC
        3. Read output bytes
        4. Cleanup
        """
        async with self._lock:
            # Use /dev/shm (Linux Shared Memory) for zero-latency IO
            # Fallback to /tmp if on Windows/Mac
            temp_dir = "/dev/shm" if os.path.exists("/dev/shm") else "/tmp"
            run_id = uuid.uuid4().hex
            
            input_path = os.path.join(temp_dir, f"in_{run_id}.wav")
            output_path = os.path.join(temp_dir, f"out_{run_id}.wav")
            
            # Write Input
            with open(input_path, "wb") as f:
                f.write(audio_bytes)
            
            # Run Inference (in thread pool to not block event loop)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                self.executor,
                self._infer_sync,
                input_path,
                output_path
            )
            
            # Read Output
            if not os.path.exists(output_path):
                raise RuntimeError("RVC Inference failed to produce output.")
                
            with open(output_path, "rb") as f:
                processed_bytes = f.read()
                
            # Cleanup (Fire and forget)
            try:
                os.remove(input_path)
                os.remove(output_path)
            except:
                pass
                
            return processed_bytes

    def _infer_sync(self, input_path, output_path):
        """Blocking GPU call"""
        self.rvc.infer_file(
            input_path=input_path,
            output_path=output_path,
            algorithm=settings.F0_METHOD,
            f0_up_key=settings.F0_UP_KEY,
            index_rate=settings.INDEX_RATE,
            filter_radius=settings.FILTER_RADIUS,
            resample_sr=0,
            rms_mix_rate=settings.RMS_MIX_RATE,
            protect=settings.PROTECT
        )

engine = RVCEngine()