"""
Automatic Subtitles Generation Module
Generates SRT/VTT subtitles from transcriptions with styling options.
"""

from typing import List, Dict, Optional
import pysrt
import webvtt
from transcriber import transcribe_video
import os


def generate_srt(
    word_map: List[Dict],
    output_path: str,
    max_chars_per_line: int = 42,
    max_lines: int = 2,
    merge_gap: float = 0.5
) -> str:
    """
    Generate SRT subtitle file from word map.
    
    Args:
        word_map: List of word dictionaries with timestamps
        output_path: Output SRT file path
        max_chars_per_line: Maximum characters per subtitle line
        max_lines: Maximum lines per subtitle
        merge_gap: Maximum gap between words to merge (seconds)
    
    Returns:
        Path to generated SRT file
    """
    subs = pysrt.SubRipFile()
    
    current_subtitle_words = []
    current_start = None
    current_end = None
    subtitle_index = 1
    
    for i, word_data in enumerate(word_map):
        word = word_data['word'].strip()
        start = word_data['start']
        end = word_data['end']
        
        # Skip punctuation-only words
        if not word or word in '.,!?;:':
            continue
        
        # Initialize or check gap
        if current_start is None:
            current_start = start
            current_subtitle_words = [word]
        else:
            gap = start - current_end
            current_text = ' '.join(current_subtitle_words)
            
            # Check if we should start a new subtitle
            should_break = (
                len(current_text) + len(word) + 1 > max_chars_per_line * max_lines or
                gap > merge_gap
            )
            
            if should_break and current_subtitle_words:
                # Save current subtitle
                subtitle_text = format_subtitle_text(
                    current_subtitle_words,
                    max_chars_per_line,
                    max_lines
                )
                subs.append(pysrt.SubRipItem(
                    index=subtitle_index,
                    start=time_to_srt_time(current_start),
                    end=time_to_srt_time(current_end),
                    text=subtitle_text
                ))
                subtitle_index += 1
                
                # Start new subtitle
                current_start = start
                current_subtitle_words = [word]
            else:
                current_subtitle_words.append(word)
        
        current_end = end
    
    # Add final subtitle
    if current_subtitle_words:
        subtitle_text = format_subtitle_text(
            current_subtitle_words,
            max_chars_per_line,
            max_lines
        )
        subs.append(pysrt.SubRipItem(
            index=subtitle_index,
            start=time_to_srt_time(current_start),
            end=time_to_srt_time(current_end),
            text=subtitle_text
        ))
    
    subs.save(output_path, encoding='utf-8')
    return output_path


def generate_vtt(
    word_map: List[Dict],
    output_path: str,
    max_chars_per_line: int = 42,
    max_lines: int = 2,
    merge_gap: float = 0.5
) -> str:
    """
    Generate WebVTT subtitle file from word map.
    
    Args:
        word_map: List of word dictionaries with timestamps
        output_path: Output VTT file path
        max_chars_per_line: Maximum characters per subtitle line
        max_lines: Maximum lines per subtitle
        merge_gap: Maximum gap between words to merge (seconds)
    
    Returns:
        Path to generated VTT file
    """
    vtt = webvtt.WebVTT()
    
    current_subtitle_words = []
    current_start = None
    current_end = None
    
    for word_data in word_map:
        word = word_data['word'].strip()
        start = word_data['start']
        end = word_data['end']
        
        if not word or word in '.,!?;:':
            continue
        
        if current_start is None:
            current_start = start
            current_subtitle_words = [word]
        else:
            gap = start - current_end
            current_text = ' '.join(current_subtitle_words)
            
            should_break = (
                len(current_text) + len(word) + 1 > max_chars_per_line * max_lines or
                gap > merge_gap
            )
            
            if should_break and current_subtitle_words:
                subtitle_text = format_subtitle_text(
                    current_subtitle_words,
                    max_chars_per_line,
                    max_lines
                )
                caption = webvtt.Caption(
                    time_to_vtt_time(current_start),
                    time_to_vtt_time(current_end),
                    subtitle_text
                )
                vtt.captions.append(caption)
                
                current_start = start
                current_subtitle_words = [word]
            else:
                current_subtitle_words.append(word)
        
        current_end = end
    
    if current_subtitle_words:
        subtitle_text = format_subtitle_text(
            current_subtitle_words,
            max_chars_per_line,
            max_lines
        )
        caption = webvtt.Caption(
            time_to_vtt_time(current_start),
            time_to_vtt_time(current_end),
            subtitle_text
        )
        vtt.captions.append(caption)
    
    vtt.save(output_path)
    return output_path


def format_subtitle_text(words: List[str], max_chars: int, max_lines: int) -> str:
    """Format words into subtitle text with line breaks."""
    text = ' '.join(words)
    
    if len(text) <= max_chars:
        return text
    
    # Split into lines
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_len = len(word) + (1 if current_line else 0)
        
        if current_length + word_len > max_chars and current_line:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += word_len
        
        if len(lines) >= max_lines - 1:
            # Last line gets remaining words
            break
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines[:max_lines])


def time_to_srt_time(seconds: float) -> pysrt.SubRipTime:
    """Convert seconds to SRT time format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return pysrt.SubRipTime(hours, minutes, secs, millis)


def time_to_vtt_time(seconds: float) -> str:
    """Convert seconds to VTT time format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def add_subtitles_to_video(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    style: Optional[Dict] = None
) -> str:
    """
    Burn subtitles into video.
    
    Args:
        video_path: Input video path
        subtitle_path: SRT or VTT file path
        output_path: Output video path
        style: Subtitle styling options
    
    Returns:
        Output video path
    """
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
    from moviepy.video.tools.subtitles import SubtitlesClip
    
    video = VideoFileClip(video_path)
    
    # Default style
    if style is None:
        style = {
            'fontsize': 24,
            'color': 'white',
            'font': 'Arial-Bold',
            'stroke_color': 'black',
            'stroke_width': 2
        }
    
    # Generate subtitle clip
    def make_textclip(txt):
        return TextClip(
            txt,
            fontsize=style['fontsize'],
            color=style['color'],
            font=style['font'],
            stroke_color=style.get('stroke_color', 'black'),
            stroke_width=style.get('stroke_width', 2)
        )
    
    if subtitle_path.endswith('.srt'):
        subtitles = SubtitlesClip(subtitle_path, make_textclip)
    else:
        # Convert VTT to SRT temporarily
        temp_srt = subtitle_path.replace('.vtt', '.srt')
        # Simple conversion (in production, use proper VTT parser)
        subtitles = SubtitlesClip(subtitle_path, make_textclip)
    
    # Composite video with subtitles
    final = CompositeVideoClip([video, subtitles.set_position(('center', 'bottom'))])
    final.write_videofile(output_path, codec='libx264', audio_codec='aac')
    
    video.close()
    final.close()
    
    return output_path

