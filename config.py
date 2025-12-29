import os
import torch

class Config:
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_DIR = os.path.join(BASE_DIR, "models")
    
    # Model Configuration
    MODEL_NAME = "tarique"  # Name of your .pth file (without extension)
    
    # Hardware
    DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
    IS_HALF = True if "cuda" in DEVICE else False # FP16 for speed on GPU
    
    # RVC Inference Parameters
    F0_METHOD = "rmvpe"      # Best quality/speed compromise
    F0_UP_KEY = 0            # Pitch shift (0 = no change)
    INDEX_RATE = 0.75        # Strength of the accent/timbre index
    FILTER_RADIUS = 3
    RMS_MIX_RATE = 0.25
    PROTECT = 0.33

settings = Config()