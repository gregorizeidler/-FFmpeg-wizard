"""
Automatic Color Correction Module
Auto white balance, exposure correction, and LUT application.
"""

import cv2
import numpy as np
from moviepy.editor import VideoFileClip
from typing import Dict, Optional, Tuple
import os


class ColorCorrector:
    """Automatic color correction for video."""
    
    def __init__(self):
        self.luts = self._load_default_luts()
    
    def _load_default_luts(self) -> Dict[str, np.ndarray]:
        """Load default LUTs for different content types."""
        # In production, load actual .cube LUT files
        # For now, return empty dict (LUTs would be loaded from files)
        return {}
    
    def auto_white_balance(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply automatic white balance correction.
        
        Args:
            frame: Input frame (BGR format)
        
        Returns:
            White-balanced frame
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Calculate average values
        avg_a = np.mean(a)
        avg_b = np.mean(b)
        
        # Adjust channels
        a = a - (avg_a - 128)
        b = b - (avg_b - 128)
        
        # Merge and convert back
        lab = cv2.merge([l, a, b])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def correct_exposure(self, frame: np.ndarray, target_brightness: float = 0.5) -> np.ndarray:
        """
        Correct exposure to target brightness level.
        
        Args:
            frame: Input frame
            target_brightness: Target brightness (0-1)
        
        Returns:
            Exposure-corrected frame
        """
        # Convert to grayscale for brightness calculation
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        current_brightness = np.mean(gray) / 255.0
        
        # Calculate adjustment factor
        if current_brightness > 0:
            adjustment = target_brightness / current_brightness
        else:
            adjustment = 1.0
        
        # Apply gamma correction
        gamma = 1.0 / adjustment
        inv_gamma = 1.0 / gamma
        
        # Build lookup table
        table = np.array([((i / 255.0) ** inv_gamma) * 255
                         for i in np.arange(0, 256)]).astype("uint8")
        
        # Apply correction
        corrected = cv2.LUT(frame, table)
        
        return corrected
    
    def apply_lut(self, frame: np.ndarray, lut_name: str = "cinematic") -> np.ndarray:
        """
        Apply a LUT (Look-Up Table) for color grading.
        
        Args:
            frame: Input frame
            lut_name: Name of LUT to apply
        
        Returns:
            Color-graded frame
        """
        # Simplified LUT application
        # In production, load actual .cube LUT files
        
        if lut_name == "cinematic":
            # Apply cinematic look (warm, desaturated)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            
            # Reduce saturation slightly
            s = cv2.multiply(s, 0.85)
            
            # Shift hue slightly warmer
            h = cv2.add(h, 5)
            
            hsv = cv2.merge([h, s, v])
            result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            return result
        
        elif lut_name == "vlog":
            # Apply vlog look (high contrast, vibrant)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Increase contrast
            l = cv2.convertScaleAbs(l, alpha=1.2, beta=10)
            
            # Enhance color
            a = cv2.convertScaleAbs(a, alpha=1.1, beta=0)
            b = cv2.convertScaleAbs(b, alpha=1.1, beta=0)
            
            lab = cv2.merge([l, a, b])
            result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            return result
        
        elif lut_name == "corporate":
            # Apply corporate look (neutral, professional)
            # Minimal changes, just ensure good exposure
            return self.correct_exposure(frame, target_brightness=0.55)
        
        else:
            return frame
    
    def correct_frame(self, frame: np.ndarray, corrections: Dict) -> np.ndarray:
        """
        Apply all requested color corrections.
        
        Args:
            frame: Input frame
            corrections: Dictionary of correction settings
        
        Returns:
            Corrected frame
        """
        result = frame.copy()
        
        if corrections.get('white_balance', False):
            result = self.auto_white_balance(result)
        
        if corrections.get('exposure', False):
            target_brightness = corrections.get('target_brightness', 0.5)
            result = self.correct_exposure(result, target_brightness)
        
        lut_name = corrections.get('lut')
        if lut_name:
            result = self.apply_lut(result, lut_name)
        
        return result
    
    def correct_video(
        self,
        video_path: str,
        output_path: str,
        corrections: Dict,
        sample_rate: float = 0.1
    ) -> str:
        """
        Apply color corrections to entire video.
        
        Args:
            video_path: Input video path
            output_path: Output video path
            corrections: Correction settings
            sample_rate: Sample every N seconds (for performance)
        
        Returns:
            Output video path
        """
        clip = VideoFileClip(video_path)
        
        def make_frame(t):
            frame = clip.get_frame(t)
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            corrected = self.correct_frame(frame_bgr, corrections)
            frame_rgb = cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB)
            return frame_rgb
        
        corrected_clip = clip.fl(make_frame, apply_to=['video'])
        corrected_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac'
        )
        
        clip.close()
        corrected_clip.close()
        
        return output_path


def detect_content_type(video_path: str) -> str:
    """
    Detect content type to suggest appropriate LUT.
    
    Args:
        video_path: Video file path
    
    Returns:
        Content type: 'cinematic', 'vlog', 'corporate', 'neutral'
    """
    # Simplified detection based on video characteristics
    # In production, use ML model or analyze frames
    
    clip = VideoFileClip(video_path)
    
    # Sample a few frames
    sample_times = [clip.duration * 0.25, clip.duration * 0.5, clip.duration * 0.75]
    frames = [clip.get_frame(t) for t in sample_times]
    
    # Analyze color characteristics
    avg_saturation = 0
    avg_brightness = 0
    
    for frame in frames:
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        avg_saturation += np.mean(hsv[:, :, 1])
        avg_brightness += np.mean(hsv[:, :, 2])
    
    avg_saturation /= len(frames)
    avg_brightness /= len(frames)
    
    clip.close()
    
    # Simple heuristics
    if avg_saturation > 100:
        return "vlog"
    elif avg_brightness < 100:
        return "cinematic"
    else:
        return "corporate"

