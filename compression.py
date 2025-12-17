"""
Intelligent Video Compression Module
Optimizes quality vs file size for different platforms.
"""

from moviepy.editor import VideoFileClip
from typing import Dict, Optional
import os


class VideoCompressor:
    """Intelligent video compression for different platforms."""
    
    # Platform presets
    PRESETS = {
        'youtube': {
            'codec': 'libx264',
            'audio_codec': 'aac',
            'bitrate': '8M',
            'audio_bitrate': '192k',
            'resolution': (1920, 1080),
            'fps': 30,
            'crf': 23
        },
        'instagram': {
            'codec': 'libx264',
            'audio_codec': 'aac',
            'bitrate': '3M',
            'audio_bitrate': '128k',
            'resolution': (1080, 1080),  # Square
            'fps': 30,
            'crf': 23
        },
        'instagram_story': {
            'codec': 'libx264',
            'audio_codec': 'aac',
            'bitrate': '3M',
            'audio_bitrate': '128k',
            'resolution': (1080, 1920),  # Vertical
            'fps': 30,
            'crf': 23
        },
        'tiktok': {
            'codec': 'libx264',
            'audio_codec': 'aac',
            'bitrate': '2M',
            'audio_bitrate': '128k',
            'resolution': (1080, 1920),  # Vertical
            'fps': 30,
            'crf': 24
        },
        'twitter': {
            'codec': 'libx264',
            'audio_codec': 'aac',
            'bitrate': '5M',
            'audio_bitrate': '128k',
            'resolution': (1280, 720),
            'fps': 30,
            'crf': 23
        },
        'linkedin': {
            'codec': 'libx264',
            'audio_codec': 'aac',
            'bitrate': '5M',
            'audio_bitrate': '192k',
            'resolution': (1920, 1080),
            'fps': 30,
            'crf': 22
        },
        'small': {
            'codec': 'libx264',
            'audio_codec': 'aac',
            'bitrate': '1M',
            'audio_bitrate': '96k',
            'resolution': (854, 480),
            'fps': 24,
            'crf': 28
        },
        'medium': {
            'codec': 'libx264',
            'audio_codec': 'aac',
            'bitrate': '3M',
            'audio_bitrate': '128k',
            'resolution': (1280, 720),
            'fps': 30,
            'crf': 25
        },
        'high': {
            'codec': 'libx264',
            'audio_codec': 'aac',
            'bitrate': '10M',
            'audio_bitrate': '256k',
            'resolution': (1920, 1080),
            'fps': 60,
            'crf': 20
        }
    }
    
    def compress_video(
        self,
        input_path: str,
        output_path: str,
        preset: str = 'medium',
        custom_settings: Optional[Dict] = None
    ) -> str:
        """
        Compress video using preset or custom settings.
        
        Args:
            input_path: Input video path
            output_path: Output video path
            preset: Preset name or 'custom'
            custom_settings: Custom compression settings
        
        Returns:
            Output video path
        """
        clip = VideoFileClip(input_path)
        
        if preset == 'custom' and custom_settings:
            settings = custom_settings
        elif preset in self.PRESETS:
            settings = self.PRESETS[preset]
        else:
            settings = self.PRESETS['medium']
        
        # Resize if needed
        target_resolution = settings.get('resolution')
        if target_resolution and (clip.w, clip.h) != target_resolution:
            clip = clip.resize(target_resolution)
        
        # Set FPS if needed
        target_fps = settings.get('fps')
        if target_fps and clip.fps != target_fps:
            clip = clip.set_fps(target_fps)
        
        # Export with settings
        export_kwargs = {
            'codec': settings['codec'],
            'audio_codec': settings['audio_codec'],
            'bitrate': settings.get('bitrate'),
            'audio_bitrate': settings.get('audio_bitrate'),
            'verbose': False,
            'logger': None
        }
        
        # Use CRF if available (better quality control)
        if 'crf' in settings:
            export_kwargs['preset'] = 'medium'
            export_kwargs['ffmpeg_params'] = ['-crf', str(settings['crf'])]
        
        clip.write_videofile(output_path, **export_kwargs)
        
        # Get file sizes
        input_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
        output_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        compression_ratio = (1 - output_size / input_size) * 100 if input_size > 0 else 0
        
        print(f"Compression complete:")
        print(f"  Input: {input_size:.2f} MB")
        print(f"  Output: {output_size:.2f} MB")
        print(f"  Compression: {compression_ratio:.1f}%")
        
        clip.close()
        
        return output_path
    
    def estimate_output_size(self, input_path: str, preset: str = 'medium') -> float:
        """
        Estimate output file size.
        
        Args:
            input_path: Input video path
            preset: Compression preset
        
        Returns:
            Estimated size in MB
        """
        clip = VideoFileClip(input_path)
        duration = clip.duration
        
        if preset in self.PRESETS:
            settings = self.PRESETS[preset]
            bitrate_mbps = float(settings['bitrate'].replace('M', ''))
            audio_bitrate_kbps = float(settings['audio_bitrate'].replace('k', ''))
            
            # Estimate: (video_bitrate + audio_bitrate) * duration / 8
            video_size_mb = (bitrate_mbps * duration) / 8
            audio_size_mb = (audio_bitrate_kbps / 1000 * duration) / 8
            
            estimated_size = video_size_mb + audio_size_mb
        else:
            # Fallback: assume 50% compression
            input_size = os.path.getsize(input_path) / (1024 * 1024)
            estimated_size = input_size * 0.5
        
        clip.close()
        
        return estimated_size
    
    def batch_compress(
        self,
        input_paths: list,
        output_dir: str,
        preset: str = 'medium'
    ) -> list:
        """
        Compress multiple videos.
        
        Args:
            input_paths: List of input video paths
            output_dir: Output directory
            preset: Compression preset
        
        Returns:
            List of output paths
        """
        os.makedirs(output_dir, exist_ok=True)
        output_paths = []
        
        for input_path in input_paths:
            filename = os.path.basename(input_path)
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{name}_compressed{ext}")
            
            self.compress_video(input_path, output_path, preset)
            output_paths.append(output_path)
        
        return output_paths

