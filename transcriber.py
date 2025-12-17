"""
Video Transcription Module
Uses Faster-Whisper to transcribe audio with word-level timestamps.
"""

from faster_whisper import WhisperModel
import os
from typing import List, Dict


def transcribe_video(audio_path: str, model_size: str = None, device: str = None) -> List[Dict]:
    """
    Transcribe audio file and return word-level timestamps.
    
    Args:
        audio_path: Path to the audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
        device: Device to use ('cpu' or 'cuda')
    
    Returns:
        List of dictionaries with word, start, end, and confidence
    """
    # Get model size and device from environment or use defaults
    model_size = model_size or os.getenv("WHISPER_MODEL", "small")
    device = device or os.getenv("WHISPER_DEVICE", "cpu")
    
    # Initialize Whisper model
    # Use int8 for CPU, float16 for CUDA
    compute_type = "int8" if device == "cpu" else "float16"
    
    print(f"Loading Whisper model '{model_size}' on {device}...")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    
    print(f"Transcribing audio: {audio_path}")
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,  # Voice Activity Detection
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    # Extract word-level timestamps
    word_map = []
    for segment in segments:
        for word in segment.words:
            word_map.append({
                "word": word.word.strip(),
                "start": word.start,
                "end": word.end,
                "confidence": word.probability
            })
    
    print(f"Transcription complete. Found {len(word_map)} words.")
    return word_map


def detect_silence_gaps(word_map: List[Dict], min_silence_duration: float = 1.0) -> List[Dict]:
    """
    Detect silence gaps between words.
    
    Args:
        word_map: List of word dictionaries with timestamps
        min_silence_duration: Minimum duration in seconds to consider as silence
    
    Returns:
        List of silence gap dictionaries with start, end, and duration
    """
    gaps = []
    
    for i in range(len(word_map) - 1):
        current_word = word_map[i]
        next_word = word_map[i + 1]
        
        gap_start = current_word["end"]
        gap_end = next_word["start"]
        gap_duration = gap_end - gap_start
        
        if gap_duration >= min_silence_duration:
            gaps.append({
                "start": gap_start,
                "end": gap_end,
                "duration": gap_duration
            })
    
    return gaps


def detect_filler_words(word_map: List[Dict]) -> List[Dict]:
    """
    Detect common filler words and repetitions.
    
    Args:
        word_map: List of word dictionaries
    
    Returns:
        List of filler word segments to remove
    """
    filler_patterns = ["um", "uh", "ah", "er", "like", "you know", "so", "well"]
    filler_segments = []
    
    for word in word_map:
        word_lower = word["word"].lower().strip(".,!?")
        if word_lower in filler_patterns:
            filler_segments.append({
                "start": word["start"],
                "end": word["end"],
                "word": word["word"]
            })
    
    return filler_segments

