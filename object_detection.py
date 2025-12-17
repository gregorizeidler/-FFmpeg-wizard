"""
Object Detection and Tagging Module
Detects objects in video and generates SEO tags.
"""

from typing import List, Dict, Optional
import openai
import os
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip
import cv2
import numpy as np

load_dotenv()


class ObjectDetector:
    """Detects objects and generates tags for video."""
    
    def __init__(self):
        # In production, use YOLO or similar ML model
        # For now, use OpenCV's basic detection + LLM analysis
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def detect_objects_in_frame(self, frame: np.ndarray) -> List[str]:
        """
        Detect objects in a single frame.
        
        Args:
            frame: Video frame
        
        Returns:
            List of detected object names
        """
        detected = []
        
        # Detect faces
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
        if len(faces) > 0:
            detected.append("person")
        
        # In production, use YOLO or similar for more objects
        # For now, use LLM to analyze transcript for object mentions
        
        return detected
    
    def analyze_video_for_tags(
        self,
        transcript_text: str,
        video_path: str,
        sample_frames: int = 5
    ) -> Dict:
        """
        Analyze video content to generate tags and metadata.
        
        Args:
            transcript_text: Video transcript
            video_path: Video file path
            sample_frames: Number of frames to sample
        
        Returns:
            Dictionary with tags, objects, and metadata
        """
        # Sample frames for visual analysis
        clip = VideoFileClip(video_path)
        sample_times = np.linspace(0, clip.duration, sample_frames)
        frames = [clip.get_frame(t) for t in sample_times]
        clip.close()
        
        # Detect objects in frames
        all_objects = set()
        for frame in frames:
            objects = self.detect_objects_in_frame(frame)
            all_objects.update(objects)
        
        # Use LLM to analyze transcript and generate tags
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                'tags': [],
                'objects': list(all_objects),
                'title_suggestion': None,
                'description': None
            }
        
        client = openai.OpenAI(api_key=api_key)
        
        try:
            prompt = f"""Analyze this video transcript and generate:
1. 10-15 relevant SEO tags (comma-separated)
2. A catchy title suggestion
3. A brief description (2-3 sentences)
4. Main topics discussed

Transcript:
{transcript_text[:2000]}  # Limit to avoid token limits

Return JSON format:
{{
    "tags": ["tag1", "tag2", ...],
    "title": "Suggested Title",
    "description": "Video description",
    "topics": ["topic1", "topic2", ...]
}}"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a video SEO expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            import json
            content = response.choices[0].message.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(content)
            
            return {
                'tags': analysis.get('tags', []),
                'objects': list(all_objects),
                'title_suggestion': analysis.get('title'),
                'description': analysis.get('description'),
                'topics': analysis.get('topics', [])
            }
            
        except Exception as e:
            print(f"Error generating tags: {e}")
            return {
                'tags': [],
                'objects': list(all_objects),
                'title_suggestion': None,
                'description': None
            }
    
    def extract_keywords(self, transcript_text: str, top_n: int = 10) -> List[str]:
        """
        Extract most important keywords from transcript.
        
        Args:
            transcript_text: Video transcript
            top_n: Number of keywords to return
        
        Returns:
            List of keywords
        """
        # Simple keyword extraction (in production, use NLP libraries)
        words = transcript_text.lower().split()
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
        
        filtered_words = [w.strip('.,!?;:()[]{}"\'-') for w in words if w.lower() not in stop_words and len(w) > 3]
        
        # Count frequency
        from collections import Counter
        word_freq = Counter(filtered_words)
        
        # Return top N
        return [word for word, count in word_freq.most_common(top_n)]


def generate_seo_metadata(video_path: str, transcript_text: str) -> Dict:
    """
    Generate complete SEO metadata for video.
    
    Args:
        video_path: Video file path
        transcript_text: Video transcript
    
    Returns:
        Complete SEO metadata dictionary
    """
    detector = ObjectDetector()
    analysis = detector.analyze_video_for_tags(transcript_text, video_path)
    keywords = detector.extract_keywords(transcript_text)
    
    return {
        **analysis,
        'keywords': keywords,
        'word_count': len(transcript_text.split()),
        'estimated_duration': None  # Would be filled from video metadata
    }

