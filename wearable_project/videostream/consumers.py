import cv2
import numpy as np
import base64
import json
import os
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import StopConsumer
import asyncio
import time
from .model_interface import get_classifier

# Configure logging
logger = logging.getLogger(__name__)

class VideoStreamConsumer(AsyncWebsocketConsumer):
    # Setup frame processing frequency
    FRAME_PROCESS_INTERVAL = 10  # Process every 3rd frame instead of 5th for better responsiveness

    async def connect(self):
        await self.accept()
        self.frame_count = 0
        self.running = True
        self.paused = False
        self.webcam_mode = False  # Flag to indicate if we're processing webcam frames
        self.start_time = time.time()
        self.last_prediction = None
        self.prediction_cache = {}  # Cache for recent predictions
        self.last_status_update = 0  # Track when we last sent status updates
        
        # Initialize variables for video capture
        self.cap = None
        self.model = get_classifier()
        
        # Start the video streaming and processing task
        self.task = asyncio.create_task(self.process_video())
        logger.info("WebSocket connection established")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection with proper cleanup"""
        logger.info(f"WebSocket disconnected with code: {close_code}")
        # Stop the main processing loop
        self.running = False
        self.paused = True  # Ensure paused state to prevent new processing
        self.webcam_mode = False
        
        # Cancel the task gracefully
        if hasattr(self, 'task') and self.task:
            try:
                self.task.cancel()
                try:
                    await asyncio.wait_for(self.task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass  # Expected during cancellation
            except Exception as e:
                logger.error(f"Error canceling task: {e}")
        
        # Release video capture resources
        if hasattr(self, 'cap') and self.cap and self.cap.isOpened():
            try:
                self.cap.release()
                logger.info("Video resources released on disconnect")
            except Exception as e:
                logger.error(f"Error releasing video capture: {e}")
        
        # Clear any large objects from memory
        self.prediction_cache = {}
        self.last_prediction = None
        
        # Raise StopConsumer to ensure proper cleanup by Channels
        raise StopConsumer()

    async def process_video(self):
        """Process video frames and run model inference"""
        try:
            # Skip video setup if we're in webcam mode
            if not self.webcam_mode:
                # Get video file path from demo directory
                # First try to find a demo video in the model directory
                video_path = None
                demo_dir = os.path.join('demo')
                
                # Look for common video files in the demo directory
                if os.path.exists(demo_dir):
                    for file in os.listdir(demo_dir):
                        if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                            video_path = os.path.join(demo_dir, file)
                            logger.info(f"Found video file: {video_path}")
                            break
                
                # If no video found in demo directory, try a sample video path
                if not video_path:
                    # Try multiple possible paths for different environments
                    possible_paths = [
                        # For Windows
                        r"demo/test.mp4",
                        # A backup sample if available
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.mp4')
                    ]
                    
                    for path in possible_paths:
                        if os.path.exists(path):
                            video_path = path
                            logger.info(f"Using backup video path: {video_path}")
                            break
                
                # If still no video file found, fall back to camera
                if not video_path:
                    logger.warning("No video file found, falling back to camera")
                    self.cap = cv2.VideoCapture(0)
                else:
                    logger.info(f"Using video file: {video_path}")
                    self.cap = cv2.VideoCapture(video_path)
                
                # Check if video opened successfully
                if not self.cap.isOpened():
                    logger.error("Could not open video source")
                    await self.send(text_data=json.dumps({
                        'error': 'Could not open video source',
                        'timestamp': time.time()
                    }))
                    return
                
                # Get video properties
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                frame_delay = 1.0 / fps if fps > 0 else 0.033  # Default to 30fps if not available
            else:
                # In webcam mode, we don't need a local video source
                frame_delay = 0.033  # ~30fps for webcam processing
            
            # Notify client about successful connection
            await self.send(text_data=json.dumps({
                'status': 'connected',
                'fps': fps if not self.webcam_mode and 'fps' in locals() else 30,
                'webcam_mode': self.webcam_mode,
                'timestamp': time.time()
            }))
            
            while self.running:
                # If paused, just sleep and continue the loop without processing
                if self.paused:
                    await asyncio.sleep(0.5)  # Sleep longer when paused to reduce CPU usage
                    continue
                
                # In webcam mode, the frames come from the browser, so we just sleep
                if self.webcam_mode:
                    await asyncio.sleep(frame_delay)
                    continue
                
                # Read frame from video - only in backend mode
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_count) 
                ret, frame = self.cap.read()
                
                # If frame is not read successfully (end of video), loop back to beginning
                if not ret:
                    logger.info("End of video file reached, stopping...")
                    self.disconnect("0")
                    break
                
                # Increment frame counter
                self.frame_count += self.FRAME_PROCESS_INTERVAL
                
                # Process frames at specified interval to reduce computational load
                if self.frame_count % self.FRAME_PROCESS_INTERVAL == 0:
                    # Check again if paused before heavy processing
                    if self.paused:
                        continue
                    
                    # Process the frame
                    await self.process_frame(frame)
                
                # Control frame rate to match video FPS
                await asyncio.sleep(frame_delay)
                
        except asyncio.CancelledError:
            # Handle task cancellation
            logger.info("Video streaming task canceled")
        except Exception as e:
            logger.error(f"Error in process_video: {e}", exc_info=True)
            # Notify client about the error
            await self.send(text_data=json.dumps({
                'error': str(e),
                'timestamp': time.time()
            }))
        finally:
            # Release resources
            if self.cap and self.cap.isOpened():
                try:
                    self.cap.release()
                    logger.info("Video resource released")
                except Exception as e:
                    logger.error(f"Error releasing video capture: {e}")
    
    async def process_frame(self, frame):
        """Process a video frame (either from backend or webcam) and send results to client"""
        try:
            # Send system status information periodically (every 5 seconds)
            current_time = time.time()
            if current_time - self.last_status_update >= 5:
                try:
                    # Get video resolution from frame or cap if available
                    if frame is not None and hasattr(frame, 'shape'):
                        height, width = frame.shape[:2]
                        resolution = f"{width}x{height}"
                    elif not self.webcam_mode and self.cap and self.cap.isOpened():
                        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        resolution = f"{width}x{height}"
                    else:
                        resolution = "Unknown"
                    
                    # Get model info
                    model_info = self.model.get_model_info()
                    
                    # Create status message
                    status_message = {
                        'status_update': True,
                        'model_info': model_info['model_name'],
                        'resolution': resolution,
                        'avg_inference_time': model_info['avg_inference_time'],
                        'paused': self.paused,  # Include pause state in status updates
                        'webcam_mode': self.webcam_mode,  # Include webcam mode state
                        'timestamp': time.time()
                    }
                    
                    # Send status update
                    await self.send(text_data=json.dumps(status_message))
                    self.last_status_update = current_time
                except Exception as e:
                    logger.error(f"Error sending status update: {e}")
            
            # Check if frame is valid before processing
            if frame is None or not isinstance(frame, np.ndarray):
                logger.error("Invalid frame received from video source")
                await self.send(text_data=json.dumps({
                    'error': "Invalid frame received from video source",
                    'timestamp': time.time()
                }))
                return
            
            # Get frame dimensions for validation
            height, width = frame.shape[:2]
            if width <= 0 or height <= 0:
                logger.error(f"Invalid frame dimensions: {width}x{height}")
                return
                
            # Start time measurement for model inference
            start_time = time.time()
            
            # Run model prediction
            pred_class, confidence_scores = self.model.predict(frame)
            inference_time = time.time() - start_time
            
            # Store prediction in cache
            self.last_prediction = {
                'class': pred_class,
                'scores': confidence_scores,
                'time': time.time()
            }
            
            # Prepare confidence scores for frontend
            confidence_list = [confidence_scores.get(cls, 0) for cls in self.model.CLASSES]
            
            # Encode frame as base64 for transmission
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])  # Quality 85% for better performance
            img_str = base64.b64encode(buffer).decode('utf-8')
            
            # Calculate elapsed time for video playback
            elapsed_time = time.time() - self.start_time
            
            # Create the message with all required data
            message = {
                'image': img_str,
                'stage': pred_class,
                'confidences': confidence_list,
                'inference_time': round(inference_time * 1000, 2),  # in milliseconds
                'timestamp': time.time(),
                'elapsed_time': round(elapsed_time, 2),  # seconds since start
                'webcam_mode': self.webcam_mode  # Include webcam mode state
            }
            
            # Send to client
            await self.send(text_data=json.dumps(message))
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            # If prediction fails but we have a previous one, use it
            if self.last_prediction and time.time() - self.last_prediction['time'] < 5.0:
                # Use cached prediction if available and recent
                try:
                    confidence_list = [self.last_prediction['scores'].get(cls, 0) for cls in self.model.CLASSES]
                    
                    # Encode frame as base64 for transmission
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    img_str = base64.b64encode(buffer).decode('utf-8')
                    
                    # Calculate elapsed time for video playback
                    elapsed_time = time.time() - self.start_time
                    
                    # Create the message with cached prediction
                    message = {
                        'image': img_str,
                        'stage': self.last_prediction['class'],
                        'confidences': confidence_list,
                        'inference_time': 0,  # No new inference
                        'timestamp': time.time(),
                        'elapsed_time': round(elapsed_time, 2),
                        'cached': True,  # Indicate this is from cache
                        'webcam_mode': self.webcam_mode
                    }
                    
                    await self.send(text_data=json.dumps(message))
                except Exception as inner_e:
                    logger.error(f"Error sending cached prediction: {inner_e}")
                    await self.send(text_data=json.dumps({
                        'error': str(inner_e),
                        'timestamp': time.time()
                    }))
            else:
                # Send error to client
                await self.send(text_data=json.dumps({
                    'error': str(e),
                    'timestamp': time.time()
                }))

    async def received_message(self, text_data):
        """Handle received messages from client"""
        try:
            data = json.loads(text_data)
            
            # Handle client commands
            if 'command' in data:
                command = data['command']
                
                if command == 'pause':
                    # Implement pause logic
                    self.paused = True
                    logger.info("Video processing paused")
                elif command == 'resume':
                    # Implement resume logic
                    self.paused = False
                    logger.info("Video processing resumed")
                elif command == 'switch_to_webcam':
                    # Switch to webcam mode
                    self.webcam_mode = True
                    self.paused = True  # Pause backend video processing
                    logger.info("Switched to webcam mode")
                elif command == 'switch_to_backend':
                    # Switch back to backend mode
                    self.webcam_mode = False
                    self.paused = False  # Resume backend video processing
                    logger.info("Switched to backend mode")
                
                # Acknowledge the command
                await self.send(text_data=json.dumps({
                    'command_ack': command,
                    'status': 'success',
                    'paused': self.paused,
                    'webcam_mode': self.webcam_mode,
                    'timestamp': time.time()
                }))
                
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            await self.send(text_data=json.dumps({
                'error': f"Failed to process message: {str(e)}",
                'timestamp': time.time()
            }))

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming messages from WebSocket clients"""
        try:
            # Handle binary data (webcam frames)
            if bytes_data:
                if not self.webcam_mode:
                    logger.warning("Received bytes data but not in webcam mode, ignoring")
                    return
                    
                try:
                    # Convert bytes to numpy array/image
                    nparr = np.frombuffer(bytes_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    # Process the frame
                    if frame is not None:
                        await self.process_frame(frame)
                    else:
                        logger.error("Failed to decode webcam frame")
                except Exception as e:
                    logger.error(f"Error processing webcam frame: {e}")
            
            # Handle text data (commands)
            elif text_data:
                await self.received_message(text_data)
                
        except Exception as e:
            logger.error(f"Error in receive method: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Server error processing your request',
                'timestamp': time.time()
            }))