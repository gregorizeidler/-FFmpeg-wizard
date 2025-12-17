"""
Main Video Editor Module
Orchestrates all editing operations: silence removal, zoom effects, B-Roll insertion.
"""

from moviepy.editor import (
    VideoFileClip,
    concatenate_videoclips,
    CompositeVideoClip,
    AudioFileClip,
    ImageClip
)
from typing import List, Dict, Optional
import os
import requests
from transcriber import transcribe_video, detect_silence_gaps, detect_filler_words
from face_tracking import FaceTracker
import tempfile


class VideoEditor:
    """Main video editing class that orchestrates all operations."""
    
    def __init__(self, input_video_path: str):
        self.input_path = input_video_path
        self.video = VideoFileClip(input_video_path)
        try:
            self.face_tracker = FaceTracker()
        except Exception as e:
            print(f"Warning: Face tracking unavailable: {e}")
            self.face_tracker = None
        self.temp_files = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary files."""
        self.video.close()
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Warning: Could not delete temp file {temp_file}: {e}")
    
    def extract_audio(self) -> str:
        """Extract audio from video to temporary file."""
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_audio_path = temp_audio.name
        temp_audio.close()
        
        self.video.audio.write_audiofile(temp_audio_path, verbose=False, logger=None)
        self.temp_files.append(temp_audio_path)
        return temp_audio_path
    
    def remove_silence(
        self,
        word_map: List[Dict],
        min_silence_duration: float = 1.0,
        padding: float = 0.2
    ) -> VideoFileClip:
        """
        Remove silence gaps from video based on word timestamps.
        
        Args:
            word_map: List of word dictionaries with timestamps
            min_silence_duration: Minimum silence duration to cut (seconds)
            padding: Padding around cuts (seconds)
        
        Returns:
            Edited video clip with silence removed
        """
        if not word_map:
            return self.video
        
        clips = []
        current_segment_start = max(0, word_map[0]['start'] - padding)
        
        for i in range(len(word_map) - 1):
            word = word_map[i]
            next_word = word_map[i + 1]
            
            gap = next_word['start'] - word['end']
            
            # If gap is large enough, cut here
            if gap >= min_silence_duration:
                end_time = min(word['end'] + padding, self.video.duration)
                
                if end_time > current_segment_start:
                    try:
                        clip_segment = self.video.subclip(current_segment_start, end_time)
                        clips.append(clip_segment)
                    except Exception as e:
                        print(f"Warning: Could not create clip segment: {e}")
                
                current_segment_start = max(0, next_word['start'] - padding)
        
        # Add the final segment
        if current_segment_start < self.video.duration:
            try:
                final_clip = self.video.subclip(current_segment_start, self.video.duration)
                clips.append(final_clip)
            except Exception as e:
                print(f"Warning: Could not create final clip segment: {e}")
        
        if not clips:
            return self.video
        
        # Concatenate all clips
        edited_video = concatenate_videoclips(clips, method="compose")
        return edited_video
    
    def remove_filler_words(
        self,
        filler_segments: List[Dict],
        padding: float = 0.1
    ) -> VideoFileClip:
        """
        Remove filler words from video.
        
        Args:
            filler_segments: List of filler word segments to remove
            padding: Padding around cuts
        
        Returns:
            Edited video clip
        """
        if not filler_segments:
            return self.video
        
        # Sort by start time
        filler_segments = sorted(filler_segments, key=lambda x: x['start'])
        
        clips = []
        last_end = 0.0
        
        for filler in filler_segments:
            start_time = max(0, filler['start'] - padding)
            end_time = min(filler['end'] + padding, self.video.duration)
            
            # Add clip before filler
            if start_time > last_end:
                try:
                    clips.append(self.video.subclip(last_end, start_time))
                except Exception as e:
                    print(f"Warning: Could not create clip segment: {e}")
            
            last_end = end_time
        
        # Add final segment
        if last_end < self.video.duration:
            try:
                clips.append(self.video.subclip(last_end, self.video.duration))
            except Exception as e:
                print(f"Warning: Could not create final clip segment: {e}")
        
        if not clips:
            return self.video
        
        edited_video = concatenate_videoclips(clips, method="compose")
        return edited_video
    
    def apply_punch_in_zoom(
        self,
        clip: VideoFileClip,
        zoom_factor: float = 1.1,
        face_center: Optional[tuple] = None
    ) -> VideoFileClip:
        """
        Apply punch-in zoom effect to a clip.
        If face_center is provided, zoom focuses on the face.
        
        Args:
            clip: Video clip to zoom
            zoom_factor: Zoom multiplier (1.1 = 10% zoom)
            face_center: Optional (x, y) face center coordinates
        
        Returns:
            Zoomed video clip
        """
        if face_center:
            # Zoom centered on face
            x1, y1, x2, y2 = self.face_tracker.calculate_zoom_region(
                clip.w,
                clip.h,
                face_center,
                zoom_factor
            )
            return clip.crop(x1=x1, y1=y1, x2=x2, y2=y2).resize((clip.w, clip.h))
        else:
            # Simple center zoom
            return clip.resize(zoom_factor).crop(
                x_center=clip.w // 2,
                y_center=clip.h // 2,
                width=clip.w,
                height=clip.h
            )
    
    def download_broll_video(self, video_url: str) -> str:
        """Download B-Roll video from URL to temporary file."""
        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_video_path = temp_video.name
        temp_video.close()
        
        try:
            response = requests.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(temp_video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.temp_files.append(temp_video_path)
            return temp_video_path
        except Exception as e:
            print(f"Error downloading B-Roll video: {e}")
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            raise
    
    def insert_broll(
        self,
        main_clip: VideoFileClip,
        broll_suggestions: List[Dict]
    ) -> VideoFileClip:
        """
        Insert B-Roll videos into the main video.
        
        Args:
            main_clip: Main video clip
            broll_suggestions: List of B-Roll suggestions with video URLs
        
        Returns:
            Composite video with B-Roll inserted
        """
        if not broll_suggestions:
            return main_clip
        
        clips_to_composite = [main_clip]
        
        for broll in broll_suggestions:
            video_url = broll.get('video_url')
            timestamp_start = broll.get('timestamp_start', 0)
            duration = broll.get('duration', 5)
            
            if not video_url:
                continue
            
            try:
                # Download B-Roll video
                broll_path = self.download_broll_video(video_url)
                broll_clip = VideoFileClip(broll_path)
                
                # Resize to match main video dimensions
                broll_clip = broll_clip.resize((main_clip.w, main_clip.h))
                
                # Trim to desired duration
                if broll_clip.duration > duration:
                    broll_clip = broll_clip.subclip(0, duration)
                
                # Set position and timing
                broll_clip = broll_clip.set_start(timestamp_start).set_position('center')
                
                clips_to_composite.append(broll_clip)
                
            except Exception as e:
                print(f"Warning: Could not insert B-Roll at {timestamp_start}s: {e}")
                continue
        
        # Composite all clips
        final_video = CompositeVideoClip(clips_to_composite)
        return final_video
    
    def process_video(
        self,
        remove_silences: bool = True,
        remove_fillers: bool = True,
        apply_zoom: bool = True,
        insert_broll: bool = False,
        broll_suggestions: Optional[List[Dict]] = None,
        min_silence_duration: float = 1.0
    ) -> VideoFileClip:
        """
        Main processing function that applies all editing operations.
        
        Args:
            remove_silences: Whether to remove silence gaps
            remove_fillers: Whether to remove filler words
            apply_zoom: Whether to apply punch-in zoom on cuts
            insert_broll: Whether to insert B-Roll videos
            broll_suggestions: List of B-Roll suggestions
            min_silence_duration: Minimum silence duration to cut
        
        Returns:
            Fully edited video clip
        """
        # Extract audio and transcribe
        print("Extracting audio...")
        audio_path = self.extract_audio()
        
        print("Transcribing video...")
        word_map = transcribe_video(audio_path)
        
        if not word_map:
            print("Warning: No words detected in video. Returning original.")
            return self.video
        
        # Get transcript text for B-Roll analysis
        transcript_text = " ".join([w['word'] for w in word_map])
        
        # Remove silences
        edited_video = self.video
        if remove_silences:
            print("Removing silences...")
            edited_video = self.remove_silence(word_map, min_silence_duration)
        
        # Remove filler words
        if remove_fillers:
            print("Removing filler words...")
            filler_segments = detect_filler_words(word_map)
            if filler_segments:
                edited_video = self.remove_filler_words(filler_segments)
        
        # Apply zoom effects on jump cuts
        if apply_zoom:
            print("Applying punch-in zoom effects...")
            # Detect jump cuts (where we removed silence)
            silence_gaps = detect_silence_gaps(word_map, min_silence_duration)
            
            if silence_gaps:
                # For each jump cut, apply zoom to the following segment
                # This is simplified - in production, you'd track segments more carefully
                try:
                    # Get face center for first frame
                    face_center = None
                    if self.face_tracker:
                        face_center = self.face_tracker.get_face_center(
                            self.input_path,
                            edited_video.duration / 2  # Sample middle of video
                        )
                    
                    # Apply zoom to entire clip (simplified approach)
                    edited_video = self.apply_punch_in_zoom(
                        edited_video,
                        zoom_factor=1.05,  # Subtle zoom
                        face_center=face_center
                    )
                except Exception as e:
                    print(f"Warning: Could not apply zoom effect: {e}")
        
        # Insert B-Roll
        if insert_broll and broll_suggestions:
            print("Inserting B-Roll videos...")
            edited_video = self.insert_broll(edited_video, broll_suggestions)
        
        return edited_video
    
    def export_video(self, clip: VideoFileClip, output_path: str, **kwargs):
        """
        Export edited video to file.
        
        Args:
            clip: Video clip to export
            output_path: Output file path
            **kwargs: Additional arguments for write_videofile
        """
        default_kwargs = {
            "codec": "libx264",
            "audio_codec": "aac",
            "temp_audiofile": "temp-audio.m4a",
            "remove_temp": True,
            "verbose": False,
            "logger": None
        }
        default_kwargs.update(kwargs)
        
        print(f"Exporting video to {output_path}...")
        clip.write_videofile(output_path, **default_kwargs)
        print("Export complete!")

