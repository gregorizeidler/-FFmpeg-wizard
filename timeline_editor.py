"""
Visual Timeline Editor Module
Timeline-based editing interface (simplified version for Streamlit).
"""

from typing import List, Dict, Optional
from moviepy.editor import VideoFileClip
import streamlit as st
import pandas as pd


class TimelineSegment:
    """Represents a segment in the timeline."""
    
    def __init__(self, start: float, end: float, clip_type: str = "video", source: Optional[str] = None):
        self.start = start
        self.end = end
        self.duration = end - start
        self.clip_type = clip_type  # 'video', 'broll', 'transition'
        self.source = source
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'start': self.start,
            'end': self.end,
            'duration': self.duration,
            'type': self.clip_type,
            'source': self.source
        }


class TimelineEditor:
    """Visual timeline editor for video."""
    
    def __init__(self):
        self.segments: List[TimelineSegment] = []
        self.video_duration = 0
    
    def load_video(self, video_path: str):
        """Load video and get duration."""
        clip = VideoFileClip(video_path)
        self.video_duration = clip.duration
        clip.close()
    
    def add_segment(self, start: float, end: float, clip_type: str = "video", source: Optional[str] = None):
        """Add segment to timeline."""
        segment = TimelineSegment(start, end, clip_type, source)
        self.segments.append(segment)
        self.segments.sort(key=lambda s: s.start)
    
    def remove_segment(self, index: int):
        """Remove segment from timeline."""
        if 0 <= index < len(self.segments):
            del self.segments[index]
    
    def get_timeline_dataframe(self) -> pd.DataFrame:
        """Get timeline as pandas DataFrame for visualization."""
        data = [seg.to_dict() for seg in self.segments]
        return pd.DataFrame(data)
    
    def render_timeline_ui(self):
        """Render timeline UI in Streamlit."""
        if not self.segments:
            st.info("No segments in timeline. Add segments to start editing.")
            return
        
        df = self.get_timeline_dataframe()
        
        st.subheader("Timeline Editor")
        
        # Display timeline
        for i, segment in enumerate(self.segments):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.write(f"**Segment {i+1}** ({segment.clip_type})")
                st.progress((segment.end - segment.start) / self.video_duration)
            
            with col2:
                st.write(f"Start: {segment.start:.2f}s")
                new_start = st.number_input(
                    f"Start {i}",
                    value=segment.start,
                    min_value=0.0,
                    max_value=self.video_duration,
                    step=0.1,
                    key=f"start_{i}"
                )
                if new_start != segment.start:
                    segment.start = new_start
                    segment.duration = segment.end - segment.start
            
            with col3:
                st.write(f"End: {segment.end:.2f}s")
                new_end = st.number_input(
                    f"End {i}",
                    value=segment.end,
                    min_value=0.0,
                    max_value=self.video_duration,
                    step=0.1,
                    key=f"end_{i}"
                )
                if new_end != segment.end:
                    segment.end = new_end
                    segment.duration = segment.end - segment.start
            
            with col4:
                if st.button("Delete", key=f"delete_{i}"):
                    self.remove_segment(i)
                    st.rerun()
        
        # Timeline visualization
        st.subheader("Timeline Visualization")
        timeline_data = []
        for seg in self.segments:
            timeline_data.append({
                'Start': seg.start,
                'End': seg.end,
                'Type': seg.clip_type,
                'Duration': seg.duration
            })
        
        if timeline_data:
            timeline_df = pd.DataFrame(timeline_data)
            st.bar_chart(timeline_df.set_index('Start')['Duration'])
    
    def export_edl(self, output_path: str):
        """
        Export Edit Decision List (EDL).
        
        Args:
            output_path: Output EDL file path
        """
        with open(output_path, 'w') as f:
            f.write("TITLE: Video Edit\n")
            f.write("FCM: NON-DROP FRAME\n\n")
            
            for i, segment in enumerate(self.segments, 1):
                f.write(f"{i:03d}  AX       V     C        {segment.start:09.2f} {segment.end:09.2f} ")
                f.write(f"{segment.start:09.2f} {segment.end:09.2f}\n")
    
    def create_video_from_timeline(self, source_video_path: str, output_path: str) -> str:
        """
        Create final video from timeline.
        
        Args:
            source_video_path: Source video path
            output_path: Output video path
        
        Returns:
            Output video path
        """
        from moviepy.editor import concatenate_videoclips
        
        source_clip = VideoFileClip(source_video_path)
        clips = []
        
        for segment in self.segments:
            if segment.clip_type == "video":
                clip = source_clip.subclip(segment.start, segment.end)
                clips.append(clip)
            # Handle other types (B-Roll, etc.) here
        
        if clips:
            final = concatenate_videoclips(clips, method="compose")
            final.write_videofile(output_path, codec='libx264', audio_codec='aac')
            final.close()
        
        source_clip.close()
        
        return output_path

