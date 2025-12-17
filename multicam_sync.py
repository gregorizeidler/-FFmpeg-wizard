"""
Multi-Camera Synchronization Module
Syncs multiple camera angles using audio fingerprinting.
"""

from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
from typing import List, Dict, Tuple
import numpy as np
import librosa
from scipy import signal
import os


class MultiCamSyncer:
    """Synchronizes multiple camera angles."""
    
    def __init__(self):
        self.sample_rate = 22050
    
    def extract_audio_features(self, audio_path: str) -> np.ndarray:
        """
        Extract audio features for synchronization.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Audio feature vector
        """
        # Load audio
        y, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # Extract chroma features (pitch-based, robust to noise)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        
        # Extract MFCC features
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Combine features
        features = np.vstack([chroma, mfcc])
        
        return features
    
    def find_sync_offset(
        self,
        reference_audio: np.ndarray,
        target_audio: np.ndarray
    ) -> float:
        """
        Find time offset to sync target audio to reference.
        
        Args:
            reference_audio: Reference audio features
            target_audio: Target audio features
        
        Returns:
            Offset in seconds (positive = target is ahead)
        """
        # Cross-correlation to find best alignment
        correlation = signal.correlate2d(
            reference_audio,
            target_audio,
            mode='full'
        )
        
        # Find peak
        max_idx = np.unravel_index(np.argmax(correlation), correlation.shape)
        
        # Calculate offset
        offset_samples = max_idx[1] - target_audio.shape[1]
        offset_seconds = offset_samples / self.sample_rate
        
        return offset_seconds
    
    def sync_videos(
        self,
        video_paths: List[str],
        reference_index: int = 0
    ) -> List[Dict]:
        """
        Synchronize multiple video files.
        
        Args:
            video_paths: List of video file paths
            reference_index: Index of reference video
        
        Returns:
            List of sync information dictionaries
        """
        if len(video_paths) < 2:
            return []
        
        # Extract audio from all videos
        audio_paths = []
        for i, video_path in enumerate(video_paths):
            clip = VideoFileClip(video_path)
            audio_path = f"temp_audio_{i}.wav"
            clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
            audio_paths.append(audio_path)
            clip.close()
        
        # Extract features
        reference_features = self.extract_audio_features(audio_paths[reference_index])
        
        sync_info = []
        
        for i, audio_path in enumerate(audio_paths):
            if i == reference_index:
                sync_info.append({
                    'video_index': i,
                    'offset': 0.0,
                    'synced': True
                })
            else:
                target_features = self.extract_audio_features(audio_path)
                offset = self.find_sync_offset(reference_features, target_features)
                
                sync_info.append({
                    'video_index': i,
                    'offset': offset,
                    'synced': abs(offset) < 5.0  # Consider synced if offset < 5s
                })
        
        # Cleanup temp files
        for audio_path in audio_paths:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        
        return sync_info
    
    def create_multicam_edit(
        self,
        video_paths: List[str],
        sync_info: List[Dict],
        switch_times: List[float],
        output_path: str
    ) -> str:
        """
        Create multi-camera edit with automatic switching.
        
        Args:
            video_paths: List of video paths
            sync_info: Synchronization information
            switch_times: Times to switch cameras (in reference timeline)
            output_path: Output video path
        
        Returns:
            Output video path
        """
        clips = []
        current_cam = 0
        
        for switch_time in switch_times:
            # Get clip from current camera
            clip = VideoFileClip(video_paths[current_cam])
            sync_offset = sync_info[current_cam]['offset']
            
            # Adjust timing based on sync offset
            start_time = switch_times[switch_times.index(switch_time) - 1] if switch_times.index(switch_time) > 0 else 0
            end_time = switch_time
            
            # Apply sync offset
            if sync_offset != 0:
                start_time -= sync_offset
                end_time -= sync_offset
            
            # Ensure valid times
            start_time = max(0, start_time)
            end_time = min(clip.duration, end_time)
            
            if end_time > start_time:
                segment = clip.subclip(start_time, end_time)
                clips.append(segment)
            
            clip.close()
            
            # Switch to next camera
            current_cam = (current_cam + 1) % len(video_paths)
        
        # Add final segment
        if clips:
            final_clip = VideoFileClip(video_paths[current_cam])
            last_switch = switch_times[-1] if switch_times else 0
            sync_offset = sync_info[current_cam]['offset']
            start_time = max(0, last_switch - sync_offset)
            
            if start_time < final_clip.duration:
                final_segment = final_clip.subclip(start_time)
                clips.append(final_segment)
            final_clip.close()
        
        # Concatenate
        if clips:
            final = concatenate_videoclips(clips, method="compose")
            final.write_videofile(output_path, codec='libx264', audio_codec='aac')
            final.close()
        
        return output_path
    
    def create_picture_in_picture(
        self,
        main_video_path: str,
        pip_video_path: str,
        sync_info: Dict,
        pip_position: str = "bottom-right",
        pip_size: Tuple[int, int] = (320, 180),
        output_path: str = "output_pip.mp4"
    ) -> str:
        """
        Create picture-in-picture composition.
        
        Args:
            main_video_path: Main video path
            pip_video_path: Picture-in-picture video path
            sync_info: Sync information for PIP video
            pip_position: Position ('top-left', 'top-right', 'bottom-left', 'bottom-right')
            pip_size: PIP size (width, height)
            output_path: Output path
        
        Returns:
            Output video path
        """
        from moviepy.editor import ColorClip
        
        main_clip = VideoFileClip(main_video_path)
        pip_clip = VideoFileClip(pip_video_path)
        
        # Resize PIP
        pip_clip = pip_clip.resize(pip_size)
        
        # Apply sync offset
        offset = sync_info.get('offset', 0)
        if offset > 0:
            pip_clip = pip_clip.subclip(offset)
        elif offset < 0:
            # Add black frames at start
            from moviepy.editor import ColorClip
            black = ColorClip(size=pip_size, duration=abs(offset), color=(0, 0, 0))
            pip_clip = concatenate_videoclips([black, pip_clip])
        
        # Match durations
        min_duration = min(main_clip.duration, pip_clip.duration)
        main_clip = main_clip.subclip(0, min_duration)
        pip_clip = pip_clip.subclip(0, min_duration)
        
        # Set position
        positions = {
            'top-left': (10, 10),
            'top-right': (main_clip.w - pip_size[0] - 10, 10),
            'bottom-left': (10, main_clip.h - pip_size[1] - 10),
            'bottom-right': (main_clip.w - pip_size[0] - 10, main_clip.h - pip_size[1] - 10)
        }
        
        pip_clip = pip_clip.set_position(positions.get(pip_position, positions['bottom-right']))
        
        # Composite
        final = CompositeVideoClip([main_clip, pip_clip])
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        main_clip.close()
        pip_clip.close()
        final.close()
        
        return output_path

