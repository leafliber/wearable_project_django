import os
import sys
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
import torch
import logging
import time
from functools import lru_cache, wraps
import hashlib

# Configure logging
logger = logging.getLogger(__name__)

# Add the model directory to path
MODEL_DIR = Path('wearable_project/model')
if MODEL_DIR.exists():
    sys.path.append(str(MODEL_DIR))
else:
    logger.warning(f"Model directory not found at {MODEL_DIR}")

# Import mmpretrain inferencer
try:
    from mmpretrain import ImageClassificationInferencer
except ImportError:
    logger.error("mmpretrain is required. Please install it with: pip install mmpretrain")
    raise ImportError("mmpretrain is required. Please install it with: pip install mmpretrain")

def np_cache(maxsize=32):
    """
    LRU cache implementation for functions whose first parameter is a numpy array.
    Uses a hash of the array's bytes for caching, which works with all numpy arrays.
    """
    def decorator(function):
        cache = {}
        
        @wraps(function)
        def wrapper(np_array, *args, **kwargs):
            # Create a hashable key from the array content and shape
            try:
                # Create a hash from the array bytes, shape and dtype
                array_bytes = np_array.tobytes()
                array_hash = hashlib.md5(array_bytes).hexdigest()
                key = (array_hash, np_array.shape, str(np_array.dtype))
                
                # Hash the other arguments if they exist
                if args or kwargs:
                    args_key = str(args) + str(sorted(kwargs.items()))
                    args_hash = hashlib.md5(args_key.encode()).hexdigest()
                    key = key + (args_hash,)
                
                # Check if result is in cache
                if key in cache:
                    return cache[key]
                
                # Not in cache, compute the result
                result = function(np_array, *args, **kwargs)
                
                # Store in cache, managing size
                if len(cache) >= maxsize:
                    # Remove a random item if cache is full (simple approach)
                    # For a more sophisticated approach, use an LRU implementation
                    try:
                        cache.pop(next(iter(cache)))
                    except:
                        # If anything goes wrong with cache management, just clear it
                        cache.clear()
                
                cache[key] = result
                return result
            except Exception as e:
                logger.error(f"Error in np_cache: {e}")
                # If caching fails, just call the function directly
                return function(np_array, *args, **kwargs)
        
        # Add cache info and clear methods
        def cache_info():
            return {"maxsize": maxsize, "currsize": len(cache), "hits": 0, "misses": 0}  # Simplified info
        
        def cache_clear():
            cache.clear()
        
        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        
        return wrapper
    return decorator

class SurgicalPhaseClassifier:
    """Interface for the surgical phase classification model"""
    
    CLASSES = [
        'additional_injection',
        'circumcision',
        'installation',
        'marking',
        'submucosal_dissection',
        'submucosal_injection'
    ]
    
    def __init__(self):
        self.model = None
        self.last_inference_time = 0
        self.frames_processed = 0
        self.avg_inference_time = 0
        self.resolution = None
        self.model_info = None
        self.load_model()
    
    def load_model(self):
        """Load the pre-trained model"""
        try:
            torch_device = "cuda" if torch.cuda.is_available() else "cpu"
            model_config = str(MODEL_DIR / 'configs' / 'resnet' / '5757project.py')
            model_weights = str(MODEL_DIR / 'epoch_100.pth')
            
            # Check if files exist
            if not os.path.exists(model_config):
                logger.error(f"Model config not found: {model_config}")
                raise FileNotFoundError(f"Model config not found: {model_config}")
            if not os.path.exists(model_weights):
                logger.error(f"Model weights not found: {model_weights}")
                raise FileNotFoundError(f"Model weights not found: {model_weights}")
            
            start_time = time.time()
            self.model = ImageClassificationInferencer(
                model=model_config,
                pretrained=model_weights,
                device=torch_device
            )
            
            # Store model info for frontend display
            self.model_info = "ResNet (Surgical Phase)"
            
            logger.info(f"Model loaded successfully in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Error loading model: {e}", exc_info=True)
            self.model = None
    
    def preprocess_frame(self, frame):
        """Preprocess the frame for model input"""
        try:
            # Update resolution info for frontend display
            if self.resolution is None and frame is not None and hasattr(frame, 'shape'):
                self.resolution = f"{frame.shape[1]}x{frame.shape[0]}"
            
            # Convert to RGB if it's BGR (OpenCV default)
            if frame is not None and len(frame.shape) == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            return frame
        except Exception as e:
            logger.error(f"Error preprocessing frame: {e}")
            raise
    
    @np_cache(maxsize=32)
    def predict_cached(self, frame):
        """Predict surgical phase from a frame with caching"""
        try:
            if frame is None:
                logger.error("Frame is None, cannot predict")
                return "Error", {}
            
            # Get prediction
            result = self.model(frame)[0]
            
            # Extract prediction and confidence scores
            pred_class = result['pred_class']
            scores = result['pred_scores']
            
            # Convert scores to percentage
            confidence_dict = {cls: float(round(score * 100, 2)) for cls, score in zip(self.CLASSES, scores)}
            
            return pred_class, confidence_dict
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return "Error", {}
    
    def predict(self, frame):
        """
        Predict the surgical phase from a video frame
        Returns tuple of (predicted_class, confidence_scores)
        """
        if self.model is None:
            logger.warning("Model not loaded, attempting to reload")
            self.load_model()
            if self.model is None:
                return "Model not loaded", {}
        
        try:
            start_time = time.time()
            
            # Check if frame is valid
            if frame is None or not isinstance(frame, np.ndarray):
                logger.error(f"Invalid frame type: {type(frame)}")
                return "Invalid frame", {}
            
            # Preprocess the frame
            processed_frame = self.preprocess_frame(frame)
            
            # Get prediction using the cached method
            pred_class, confidence_dict = self.predict_cached(processed_frame)
            
            # Update performance metrics
            inference_time = time.time() - start_time
            self.last_inference_time = inference_time
            self.frames_processed += 1
            self.avg_inference_time = ((self.frames_processed - 1) * self.avg_inference_time + inference_time) / self.frames_processed
            
            return pred_class, confidence_dict
        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            return "Error", {}
    
    def get_model_info(self):
        """Return model information for frontend display"""
        return {
            "model_name": self.model_info or "Unknown",
            "resolution": self.resolution or "Unknown",
            "avg_inference_time": f"{self.avg_inference_time * 1000:.2f} ms" if self.avg_inference_time else "Unknown"
        }

# Singleton instance
classifier = None

def get_classifier():
    """Get or create singleton classifier instance"""
    global classifier
    if classifier is None:
        classifier = SurgicalPhaseClassifier()
    return classifier 