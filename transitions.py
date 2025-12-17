"""
Intelligent Transitions Module
Smooth transitions between cuts with motion-based effects.
"""

from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
from moviepy.video.fx import fadein, fadeout
import numpy as np
from typing import List, Dict, Optional
import cv2


def create_fade_transition(clip1: VideoFileClip, clip2: VideoFileClip, duration: float = 0.5) -> VideoFileClip:
    """
    Create a crossfade transition between two clips.
    
    Args:
        clip1: First video clip
        clip2: Second video clip
        duration: Transition duration in seconds
    
    Returns:
        Composite clip with fade transition
    """
    # Apply fade out to clip1
    clip1_faded = clip1.fx(fadeout, duration)
    
    # Apply fade in to clip2
    clip2_faded = clip2.fx(fadein, duration)
    
    # Set timing so they overlap
    clip2_faded = clip2_faded.set_start(clip1.duration - duration)
    
    # Composite
    final = CompositeVideoClip([clip1_faded, clip2_faded])
    
    return final


def create_dip_to_black(clip1: VideoFileClip, clip2: VideoFileClip, duration: float = 0.3) -> VideoFileClip:
    """
    Create a dip-to-black transition.
    
    Args:
        clip1: First video clip
        clip2: Second video clip
        duration: Transition duration
    
    Returns:
        Composite clip with dip-to-black transition
    """
    # Fade out clip1
    clip1_faded = clip1.fx(fadeout, duration)
    
    # Fade in clip2
    clip2_faded = clip2.fx(fadein, duration)
    
    # Create black frame
    black_frame = ImageClip(np.zeros((clip1.h, clip1.w, 3), dtype=np.uint8), duration=duration)
    
    # Set timing
    black_frame = black_frame.set_start(clip1.duration - duration)
    clip2_faded = clip2_faded.set_start(clip1.duration)
    
    # Composite
    final = CompositeVideoClip([clip1_faded, black_frame, clip2_faded])
    
    return final


def create_zoom_transition(clip1: VideoFileClip, clip2: VideoFileClip, duration: float = 0.5) -> VideoFileClip:
    """
    Create a zoom transition (zoom out from clip1, zoom in to clip2).
    
    Args:
        clip1: First video clip
        clip2: Second video clip
        duration: Transition duration
    
    Returns:
        Composite clip with zoom transition
    """
    # Zoom out clip1
    def zoom_out(t):
        if t < clip1.duration - duration:
            return 1.0
        progress = (t - (clip1.duration - duration)) / duration
        return 1.0 - (progress * 0.3)  # Zoom out 30%
    
    clip1_zoomed = clip1.resize(zoom_out)
    
    # Zoom in clip2
    def zoom_in(t):
        if t < duration:
            progress = t / duration
            return 0.7 + (progress * 0.3)  # Zoom from 70% to 100%
        return 1.0
    
    clip2_zoomed = clip2.resize(zoom_in)
    clip2_zoomed = clip2_zoomed.set_start(clip1.duration - duration)
    
    # Composite
    final = CompositeVideoClip([clip1_zoomed, clip2_zoomed])
    
    return final


def create_slide_transition(clip1: VideoFileClip, clip2: VideoFileClip, direction: str = "right", duration: float = 0.5) -> VideoFileClip:
    """
    Create a slide transition.
    
    Args:
        clip1: First video clip
        clip2: Second video clip
        direction: 'left', 'right', 'up', 'down'
        duration: Transition duration
    
    Returns:
        Composite clip with slide transition
    """
    def slide_position(t, clip, direction):
        if t < clip.duration - duration:
            return ('center', 'center')
        
        progress = (t - (clip.duration - duration)) / duration
        
        if direction == "right":
            x_offset = int(progress * clip.w)
            return (f'center+{x_offset}', 'center')
        elif direction == "left":
            x_offset = int(-progress * clip.w)
            return (f'center+{x_offset}', 'center')
        elif direction == "up":
            y_offset = int(-progress * clip.h)
            return ('center', f'center+{y_offset}')
        else:  # down
            y_offset = int(progress * clip.h)
            return ('center', f'center+{y_offset}')
    
    clip1_positioned = clip1.set_position(lambda t: slide_position(t, clip1, direction))
    
    # Clip2 slides in from opposite direction
    opposite_dir = {"right": "left", "left": "right", "up": "down", "down": "up"}[direction]
    
    def slide_in_position(t):
        if t < duration:
            progress = t / duration
            if opposite_dir == "right":
                x_offset = int((1 - progress) * clip2.w)
                return (f'center+{x_offset}', 'center')
            elif opposite_dir == "left":
                x_offset = int(-(1 - progress) * clip2.w)
                return (f'center+{x_offset}', 'center')
            elif opposite_dir == "up":
                y_offset = int(-(1 - progress) * clip2.h)
                return ('center', f'center+{y_offset}')
            else:  # down
                y_offset = int((1 - progress) * clip2.h)
                return ('center', f'center+{y_offset}')
        return ('center', 'center')
    
    clip2_positioned = clip2.set_position(slide_in_position)
    clip2_positioned = clip2_positioned.set_start(clip1.duration - duration)
    
    # Composite
    final = CompositeVideoClip([clip1_positioned, clip2_positioned])
    
    return final


def add_transitions_to_clips(clips: List[VideoFileClip], transition_type: str = "fade", duration: float = 0.5) -> VideoFileClip:
    """
    Add transitions between multiple clips.
    
    Args:
        clips: List of video clips
        transition_type: 'fade', 'dip_to_black', 'zoom', 'slide'
        duration: Transition duration
    
    Returns:
        Composite clip with transitions
    """
    if len(clips) == 0:
        raise ValueError("No clips provided")
    
    if len(clips) == 1:
        return clips[0]
    
    transitioned_clips = []
    
    for i in range(len(clips) - 1):
        clip1 = clips[i]
        clip2 = clips[i + 1]
        
        if transition_type == "fade":
            transition_clip = create_fade_transition(clip1, clip2, duration)
        elif transition_type == "dip_to_black":
            transition_clip = create_dip_to_black(clip1, clip2, duration)
        elif transition_type == "zoom":
            transition_clip = create_zoom_transition(clip1, clip2, duration)
        elif transition_type == "slide":
            transition_clip = create_slide_transition(clip1, clip2, "right", duration)
        else:
            transition_clip = create_fade_transition(clip1, clip2, duration)
        
        transitioned_clips.append(transition_clip)
    
    # Add final clip
    transitioned_clips.append(clips[-1])
    
    # Concatenate all
    from moviepy.editor import concatenate_videoclips
    final = concatenate_videoclips(transitioned_clips, method="compose")
    
    return final


def detect_motion_for_transition(clip: VideoFileClip, t: float) -> Dict:
    """
    Detect motion in frame to suggest transition type.
    
    Args:
        clip: Video clip
        t: Time in seconds
    
    Returns:
        Motion analysis dictionary
    """
    if t >= clip.duration:
        t = clip.duration - 0.1
    
    frame1 = clip.get_frame(max(0, t - 0.1))
    frame2 = clip.get_frame(t)
    
    # Convert to grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)
    
    # Calculate optical flow
    flow = cv2.calcOpticalFlowFarneback(gray1, gray2, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    
    # Calculate motion magnitude
    magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
    avg_magnitude = np.mean(magnitude)
    
    # Determine motion direction
    avg_flow_x = np.mean(flow[..., 0])
    avg_flow_y = np.mean(flow[..., 1])
    
    return {
        'magnitude': avg_magnitude,
        'direction_x': avg_flow_x,
        'direction_y': avg_flow_y,
        'has_motion': avg_magnitude > 5.0
    }

