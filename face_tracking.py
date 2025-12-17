"""
Face Detection and Tracking Module
Uses OpenCV to detect faces and calculate optimal zoom/crop regions.
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List, Dict
from moviepy.editor import VideoFileClip


class FaceTracker:
    """Detects and tracks faces in video frames."""
    
    def __init__(self):
        # Load Haar Cascade for face detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            raise RuntimeError("Failed to load face detection cascade")
    
    def detect_face_in_frame(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect face in a single frame.
        
        Args:
            frame: Frame as numpy array (BGR format)
        
        Returns:
            Tuple of (x, y, width, height) or None if no face found
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50)
        )
        
        if len(faces) > 0:
            # Return the largest face
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            return tuple(largest_face)
        
        return None
    
    def get_face_center(self, video_path: str, time_seconds: float) -> Optional[Tuple[int, int]]:
        """
        Get face center coordinates at a specific time in the video.
        
        Args:
            video_path: Path to video file
            time_seconds: Time in seconds
        
        Returns:
            Tuple of (center_x, center_y) or None
        """
        clip = VideoFileClip(video_path)
        
        if time_seconds >= clip.duration:
            clip.close()
            return None
        
        frame = clip.get_frame(time_seconds)
        clip.close()
        
        face = self.detect_face_in_frame(frame)
        
        if face:
            x, y, w, h = face
            center_x = x + w // 2
            center_y = y + h // 2
            return (center_x, center_y)
        
        return None
    
    def calculate_zoom_region(
        self,
        video_width: int,
        video_height: int,
        face_center: Tuple[int, int],
        zoom_factor: float = 1.1
    ) -> Tuple[int, int, int, int]:
        """
        Calculate crop region for zoom effect centered on face.
        
        Args:
            video_width: Original video width
            video_height: Original video height
            face_center: (x, y) coordinates of face center
            zoom_factor: Zoom multiplier (1.1 = 10% zoom)
        
        Returns:
            Tuple of (x1, y1, x2, y2) crop coordinates
        """
        new_width = int(video_width / zoom_factor)
        new_height = int(video_height / zoom_factor)
        
        center_x, center_y = face_center
        
        # Calculate crop box centered on face
        x1 = max(0, center_x - new_width // 2)
        y1 = max(0, center_y - new_height // 2)
        x2 = min(video_width, x1 + new_width)
        y2 = min(video_height, y1 + new_height)
        
        # Adjust if crop goes out of bounds
        if x2 - x1 < new_width:
            x1 = max(0, x2 - new_width)
        if y2 - y1 < new_height:
            y1 = max(0, y2 - new_height)
        
        return (x1, y1, x2, y2)
    
    def track_faces_in_video(self, video_path: str, sample_rate: float = 0.5) -> List[Dict]:
        """
        Track faces throughout the video at regular intervals.
        
        Args:
            video_path: Path to video file
            sample_rate: Sample every N seconds
        
        Returns:
            List of face positions at different timestamps
        """
        clip = VideoFileClip(video_path)
        face_positions = []
        
        current_time = 0.0
        while current_time < clip.duration:
            face_center = self.get_face_center(video_path, current_time)
            
            if face_center:
                face_positions.append({
                    "time": current_time,
                    "center": face_center
                })
            
            current_time += sample_rate
        
        clip.close()
        return face_positions

