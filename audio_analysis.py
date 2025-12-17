"""
Advanced Audio Analysis Module
Volume normalization, noise reduction, EQ, click/pop detection.
"""

from moviepy.editor import AudioFileClip
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import numpy as np
from scipy import signal
from typing import Dict, List, Tuple
import tempfile
import os


class AudioProcessor:
    """Advanced audio processing and analysis."""
    
    def __init__(self):
        self.sample_rate = 44100
    
    def normalize_volume(self, audio_path: str, target_dBFS: float = -20.0) -> str:
        """
        Normalize audio volume to target level.
        
        Args:
            audio_path: Input audio path
            target_dBFS: Target volume in dBFS
        
        Returns:
            Path to normalized audio file
        """
        audio = AudioSegment.from_file(audio_path)
        
        # Normalize to target level
        change_in_dBFS = target_dBFS - audio.dBFS
        normalized = audio.apply_gain(change_in_dBFS)
        
        # Export
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
        normalized.export(output_path, format="wav")
        
        return output_path
    
    def reduce_noise(self, audio_path: str, noise_reduction_db: float = 10.0) -> str:
        """
        Reduce background noise.
        
        Args:
            audio_path: Input audio path
            noise_reduction_db: Noise reduction in dB
        
        Returns:
            Path to processed audio file
        """
        audio = AudioSegment.from_file(audio_path)
        
        # Simple noise reduction using high-pass filter
        # In production, use spectral subtraction or ML-based methods
        audio = audio.high_pass_filter(80)  # Remove low-frequency noise
        
        # Apply compression to reduce dynamic range
        audio = compress_dynamic_range(audio, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
        
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
        audio.export(output_path, format="wav")
        
        return output_path
    
    def apply_eq(self, audio_path: str, eq_settings: Dict) -> str:
        """
        Apply equalization.
        
        Args:
            audio_path: Input audio path
            eq_settings: EQ settings dictionary
        
        Returns:
            Path to processed audio file
        """
        audio = AudioSegment.from_file(audio_path)
        
        # Apply frequency adjustments
        # Low frequencies (bass)
        if 'low_gain' in eq_settings:
            audio = audio.low_pass_filter(250).apply_gain(eq_settings['low_gain'])
            audio = audio + AudioSegment.from_file(audio_path).high_pass_filter(250)
        
        # Mid frequencies
        if 'mid_gain' in eq_settings:
            # Apply mid boost/cut
            pass  # More complex, would need band-pass filtering
        
        # High frequencies (treble)
        if 'high_gain' in eq_settings:
            audio = audio.high_pass_filter(4000).apply_gain(eq_settings['high_gain'])
            audio = audio + AudioSegment.from_file(audio_path).low_pass_filter(4000)
        
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
        audio.export(output_path, format="wav")
        
        return output_path
    
    def detect_clicks_pops(self, audio_path: str, threshold: float = 0.1) -> List[Dict]:
        """
        Detect clicks and pops in audio.
        
        Args:
            audio_path: Input audio path
            threshold: Detection threshold
        
        Returns:
            List of detected clicks/pops with timestamps
        """
        audio = AudioSegment.from_file(audio_path)
        samples = np.array(audio.get_array_of_samples())
        
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))
            samples = samples.mean(axis=1)  # Convert to mono
        
        # Normalize
        samples = samples / np.max(np.abs(samples))
        
        # Detect sudden changes (clicks/pops)
        diff = np.diff(samples)
        click_indices = np.where(np.abs(diff) > threshold)[0]
        
        clicks = []
        for idx in click_indices:
            time_seconds = idx / audio.frame_rate
            clicks.append({
                'time': time_seconds,
                'amplitude': abs(diff[idx]),
                'type': 'click' if diff[idx] > 0 else 'pop'
            })
        
        return clicks
    
    def remove_clicks_pops(self, audio_path: str, clicks: List[Dict]) -> str:
        """
        Remove detected clicks and pops.
        
        Args:
            audio_path: Input audio path
            clicks: List of detected clicks/pops
        
        Returns:
            Path to cleaned audio file
        """
        audio = AudioSegment.from_file(audio_path)
        
        # Simple approach: apply gentle smoothing around click locations
        # In production, use interpolation or spectral repair
        for click in clicks:
            time_ms = int(click['time'] * 1000)
            # Apply fade to smooth the transition
            fade_duration = 10  # ms
            audio = audio.fade_in(fade_duration).fade_out(fade_duration)
        
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
        audio.export(output_path, format="wav")
        
        return output_path
    
    def analyze_audio_quality(self, audio_path: str) -> Dict:
        """
        Analyze audio quality metrics.
        
        Args:
            audio_path: Input audio path
        
        Returns:
            Quality analysis dictionary
        """
        audio = AudioSegment.from_file(audio_path)
        samples = np.array(audio.get_array_of_samples())
        
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))
            samples = samples.mean(axis=1)
        
        samples = samples / np.max(np.abs(samples))
        
        # Calculate metrics
        rms = np.sqrt(np.mean(samples**2))
        peak = np.max(np.abs(samples))
        dynamic_range = peak / (rms + 1e-10)
        
        # Frequency analysis
        fft = np.fft.fft(samples)
        freqs = np.fft.fftfreq(len(samples), 1/audio.frame_rate)
        power = np.abs(fft)**2
        
        # Find dominant frequency
        dominant_freq_idx = np.argmax(power[:len(power)//2])
        dominant_freq = abs(freqs[dominant_freq_idx])
        
        return {
            'rms_level': float(rms),
            'peak_level': float(peak),
            'dynamic_range': float(dynamic_range),
            'dominant_frequency': float(dominant_freq),
            'sample_rate': audio.frame_rate,
            'channels': audio.channels,
            'duration': len(audio) / 1000.0,
            'dBFS': audio.dBFS
        }
    
    def process_audio(
        self,
        audio_path: str,
        normalize: bool = True,
        reduce_noise: bool = False,
        eq_settings: Optional[Dict] = None,
        remove_clicks: bool = False
    ) -> str:
        """
        Apply all requested audio processing.
        
        Args:
            audio_path: Input audio path
            normalize: Whether to normalize volume
            reduce_noise: Whether to reduce noise
            eq_settings: Optional EQ settings
            remove_clicks: Whether to remove clicks/pops
        
        Returns:
            Path to processed audio file
        """
        current_path = audio_path
        
        if normalize:
            current_path = self.normalize_volume(current_path)
        
        if reduce_noise:
            current_path = self.reduce_noise(current_path)
        
        if eq_settings:
            current_path = self.apply_eq(current_path, eq_settings)
        
        if remove_clicks:
            clicks = self.detect_clicks_pops(current_path)
            if clicks:
                current_path = self.remove_clicks_pops(current_path, clicks)
        
        return current_path

