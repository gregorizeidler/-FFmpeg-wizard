"""
Automatic Thumbnail Generation Module
Selects best frames and creates styled thumbnails.
"""

import cv2
import numpy as np
from moviepy.editor import VideoFileClip
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Optional, Tuple
from sentiment_analysis import detect_engagement_moments
import os


class ThumbnailGenerator:
    """Generates automatic thumbnails from video."""
    
    def __init__(self):
        self.font_path = self._find_font()
    
    def _find_font(self) -> Optional[str]:
        """Find available system font."""
        # Try common font paths
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "C:/Windows/Fonts/arial.ttf"  # Windows
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def analyze_frame_quality(self, frame: np.ndarray) -> float:
        """
        Analyze frame quality for thumbnail selection.
        
        Args:
            frame: Video frame
        
        Returns:
            Quality score (0-1)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        
        # Calculate sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        
        # Normalize (typical values 0-1000)
        sharpness_score = min(sharpness / 500.0, 1.0)
        
        # Calculate brightness (optimal around 0.5)
        brightness = np.mean(gray) / 255.0
        brightness_score = 1.0 - abs(brightness - 0.5) * 2
        
        # Calculate contrast
        contrast = np.std(gray) / 255.0
        contrast_score = min(contrast * 2, 1.0)
        
        # Combined score
        quality_score = (sharpness_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
        
        return quality_score
    
    def check_composition(self, frame: np.ndarray) -> float:
        """
        Check if frame follows rule of thirds.
        
        Args:
            frame: Video frame
        
        Returns:
            Composition score (0-1)
        """
        h, w = frame.shape[:2]
        
        # Rule of thirds grid lines
        third_w = w / 3
        third_h = h / 3
        
        # Detect faces (main subject)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)
        
        if len(faces) > 0:
            # Check if face is near rule of thirds intersection
            face = faces[0]
            face_center_x = face[0] + face[2] // 2
            face_center_y = face[1] + face[3] // 2
            
            # Distance to nearest third intersection
            intersections = [
                (third_w, third_h),
                (third_w * 2, third_h),
                (third_w, third_h * 2),
                (third_w * 2, third_h * 2)
            ]
            
            min_dist = min([
                np.sqrt((face_center_x - ix)**2 + (face_center_y - iy)**2)
                for ix, iy in intersections
            ])
            
            # Score based on distance (closer = better)
            max_dist = np.sqrt(w**2 + h**2)
            composition_score = 1.0 - (min_dist / max_dist)
            
            return composition_score
        
        return 0.5  # Neutral score if no face detected
    
    def select_best_frames(
        self,
        video_path: str,
        sentiment_segments: List[Dict],
        num_frames: int = 5,
        sample_rate: float = 1.0
    ) -> List[Dict]:
        """
        Select best frames for thumbnails.
        
        Args:
            video_path: Video file path
            sentiment_segments: High engagement moments
            num_frames: Number of frames to select
            sample_rate: Sample every N seconds
        
        Returns:
            List of selected frames with metadata
        """
        clip = VideoFileClip(video_path)
        candidate_frames = []
        
        # Prioritize high engagement moments
        engagement_times = [s['start'] for s in sentiment_segments[:10]]
        
        # Sample frames
        current_time = 0
        while current_time < clip.duration:
            # Check if this is a high engagement moment
            is_engagement = any(
                abs(current_time - et) < 2.0 for et in engagement_times
            )
            
            frame = clip.get_frame(current_time)
            quality = self.analyze_frame_quality(frame)
            composition = self.check_composition(frame)
            
            # Boost score for engagement moments
            score = (quality * 0.6 + composition * 0.4)
            if is_engagement:
                score *= 1.3
            
            candidate_frames.append({
                'time': current_time,
                'frame': frame,
                'quality': quality,
                'composition': composition,
                'score': score,
                'is_engagement': is_engagement
            })
            
            current_time += sample_rate
        
        clip.close()
        
        # Sort by score and select top frames
        candidate_frames.sort(key=lambda x: x['score'], reverse=True)
        selected = candidate_frames[:num_frames]
        
        return selected
    
    def create_thumbnail(
        self,
        frame: np.ndarray,
        title: Optional[str] = None,
        style: str = "modern"
    ) -> Image.Image:
        """
        Create styled thumbnail from frame.
        
        Args:
            frame: Video frame
            title: Optional title text
            style: Thumbnail style ('modern', 'bold', 'minimal')
        
        Returns:
            PIL Image thumbnail
        """
        # Convert to PIL Image
        img = Image.fromarray(frame)
        
        if style == "modern":
            # Add subtle overlay
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 30))
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        
        # Add title if provided
        if title and self.font_path:
            draw = ImageDraw.Draw(img)
            
            try:
                font_size = int(img.height * 0.08)
                font = ImageFont.truetype(self.font_path, font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position (centered, near bottom)
            bbox = draw.textbbox((0, 0), title, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (img.width - text_width) // 2
            y = img.height - text_height - int(img.height * 0.1)
            
            # Draw text with outline
            if style == "bold":
                # Bold style: white text with black outline
                for adj in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                    draw.text((x + adj[0], y + adj[1]), title, font=font, fill='black')
                draw.text((x, y), title, font=font, fill='white')
            else:
                # Modern style: semi-transparent background
                padding = 10
                overlay_rect = Image.new('RGBA', (text_width + padding * 2, text_height + padding * 2), (0, 0, 0, 180))
                img.paste(overlay_rect, (x - padding, y - padding), overlay_rect)
                draw.text((x, y), title, font=font, fill='white')
        
        return img
    
    def generate_thumbnails(
        self,
        video_path: str,
        sentiment_segments: List[Dict],
        output_dir: str,
        title: Optional[str] = None,
        num_variations: int = 3
    ) -> List[str]:
        """
        Generate multiple thumbnail variations.
        
        Args:
            video_path: Video file path
            sentiment_segments: Engagement moments
            output_dir: Output directory
            title: Optional title
            num_variations: Number of variations to generate
        
        Returns:
            List of output file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Select best frames
        frames = self.select_best_frames(video_path, sentiment_segments, num_variations)
        
        output_paths = []
        
        for i, frame_data in enumerate(frames):
            thumbnail = self.create_thumbnail(
                frame_data['frame'],
                title=title,
                style="modern" if i % 2 == 0 else "bold"
            )
            
            output_path = os.path.join(output_dir, f"thumbnail_{i+1}.jpg")
            thumbnail.save(output_path, quality=95)
            output_paths.append(output_path)
        
        return output_paths

