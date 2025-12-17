"""
Adaptive Background Music Module
Intelligent music selection and volume ducking based on speech.
"""

from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from typing import List, Dict, Optional
import os
import requests
import tempfile
from transcriber import transcribe_video
import numpy as np


class BackgroundMusicManager:
    """Manages background music selection and mixing."""
    
    def __init__(self):
        self.music_library = self._initialize_music_library()
    
    def _initialize_music_library(self) -> Dict[str, List[str]]:
        """
        Initialize music library by category.
        In production, this would load from a database or API.
        """
        return {
            'upbeat': [],
            'calm': [],
            'corporate': [],
            'cinematic': [],
            'tech': [],
            'vlog': []
        }
    
    def analyze_content_for_music(self, transcript_text: str, sentiment_segments: List[Dict]) -> str:
        """
        Analyze content to suggest music style.
        
        Args:
            transcript_text: Video transcript
            sentiment_segments: Sentiment analysis results
        
        Returns:
            Suggested music category
        """
        # Calculate average energy
        if sentiment_segments:
            avg_energy = np.mean([s['energy'] for s in sentiment_segments])
            
            if avg_energy > 7:
                return 'upbeat'
            elif avg_energy < 4:
                return 'calm'
            else:
                return 'corporate'
        
        # Fallback based on keywords
        text_lower = transcript_text.lower()
        
        if any(word in text_lower for word in ['excited', 'amazing', 'awesome', 'great']):
            return 'upbeat'
        elif any(word in text_lower for word in ['relax', 'peaceful', 'calm', 'meditation']):
            return 'calm'
        elif any(word in text_lower for word in ['technology', 'coding', 'software', 'tech']):
            return 'tech'
        else:
            return 'corporate'
    
    def download_music_from_pexels(self, query: str, duration: int = 60) -> Optional[str]:
        """
        Download music from Pexels (they also have audio).
        
        Args:
            query: Search query
            duration: Desired duration in seconds
        
        Returns:
            Path to downloaded audio file
        """
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return None
        
        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=1"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Note: Pexels primarily has video, not separate audio
            # In production, use a dedicated music API like Epidemic Sound, Artlist, etc.
            return None
        except Exception as e:
            print(f"Error fetching music: {e}")
            return None
    
    def apply_ducking(
        self,
        speech_audio: AudioFileClip,
        music_audio: AudioFileClip,
        word_map: List[Dict],
        duck_amount: float = 0.3,
        fade_duration: float = 0.2
    ) -> AudioFileClip:
        """
        Apply volume ducking: lower music when speech is present.
        
        Args:
            speech_audio: Speech audio clip
            music_audio: Background music clip
            word_map: Word timestamps for speech detection
            duck_amount: Volume reduction factor (0-1)
            fade_duration: Fade in/out duration
        
        Returns:
            Processed music audio with ducking
        """
        # Create speech presence mask
        speech_mask = np.zeros(int(music_audio.duration * music_audio.fps))
        
        for word in word_map:
            start_frame = int(word['start'] * music_audio.fps)
            end_frame = int(word['end'] * music_audio.fps)
            speech_mask[start_frame:end_frame] = 1.0
        
        # Create volume envelope
        def make_frame(t):
            frame_idx = int(t * music_audio.fps)
            if frame_idx < len(speech_mask) and speech_mask[frame_idx] > 0:
                # Duck when speech is present
                return duck_amount
            else:
                # Normal volume when no speech
                return 1.0
        
        # Apply volume envelope
        ducked_music = music_audio.volumex(make_frame)
        
        return ducked_music
    
    def sync_music_to_pacing(self, music_audio: AudioFileClip, pacing_analysis: Dict) -> AudioFileClip:
        """
        Adjust music tempo to match speech pacing.
        
        Args:
            music_audio: Music audio clip
            pacing_analysis: Pacing analysis results
        
        Returns:
            Adjusted music audio
        """
        # In production, use librosa for tempo adjustment
        # For now, return original
        return music_audio
    
    def mix_audio(
        self,
        speech_audio: AudioFileClip,
        music_path: Optional[str],
        word_map: List[Dict],
        music_volume: float = 0.3,
        ducking: bool = True
    ) -> AudioFileClip:
        """
        Mix speech and background music.
        
        Args:
            speech_audio: Speech audio clip
            music_path: Path to music file
            word_map: Word timestamps
            music_volume: Base music volume (0-1)
            ducking: Whether to apply ducking
        
        Returns:
            Mixed audio clip
        """
        if not music_path or not os.path.exists(music_path):
            return speech_audio
        
        music_audio = AudioFileClip(music_path)
        
        # Match duration
        if music_audio.duration < speech_audio.duration:
            # Loop music if shorter
            loops_needed = int(np.ceil(speech_audio.duration / music_audio.duration))
            music_clips = [music_audio] * loops_needed
            from moviepy.editor import concatenate_audioclips
            music_audio = concatenate_audioclips(music_clips).subclip(0, speech_audio.duration)
        else:
            music_audio = music_audio.subclip(0, speech_audio.duration)
        
        # Apply ducking if requested
        if ducking:
            music_audio = self.apply_ducking(speech_audio, music_audio, word_map)
        
        # Set base volume
        music_audio = music_audio.volumex(music_volume)
        
        # Composite
        final_audio = CompositeAudioClip([speech_audio, music_audio])
        
        return final_audio


def get_free_music_suggestion(content_type: str) -> str:
    """
    Suggest free music sources based on content type.
    
    Args:
        content_type: Type of content
    
    Returns:
        Suggestion message
    """
    suggestions = {
        'upbeat': "Try searching 'upbeat background music' on YouTube Audio Library or Freesound.org",
        'calm': "Try searching 'ambient background music' on Incompetech or Bensound",
        'corporate': "Try searching 'corporate background music' on Pixabay or Free Music Archive",
        'cinematic': "Try searching 'cinematic music' on YouTube Audio Library",
        'tech': "Try searching 'electronic background music' on Freesound.org"
    }
    
    return suggestions.get(content_type, "Search for royalty-free music matching your content style")

