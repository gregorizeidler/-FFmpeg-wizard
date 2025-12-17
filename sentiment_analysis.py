"""
Sentiment and Rhythm Analysis Module
Analyzes video content for energy levels, engagement moments, and pacing.
"""

from typing import List, Dict, Tuple
import numpy as np
from transcriber import transcribe_video
import openai
import os
from dotenv import load_dotenv

load_dotenv()


def analyze_sentiment(word_map: List[Dict], transcript_text: str) -> List[Dict]:
    """
    Analyze sentiment and energy levels throughout the video.
    
    Args:
        word_map: List of word dictionaries with timestamps
        transcript_text: Full transcript text
    
    Returns:
        List of sentiment segments with timestamps and scores
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []
    
    client = openai.OpenAI(api_key=api_key)
    
    # Split transcript into chunks for analysis
    chunk_size = 500  # words
    chunks = []
    current_chunk = []
    current_time = 0
    
    for word_data in word_map:
        current_chunk.append(word_data)
        if len(current_chunk) >= chunk_size:
            chunk_text = ' '.join([w['word'] for w in current_chunk])
            chunks.append({
                'text': chunk_text,
                'start': current_chunk[0]['start'],
                'end': current_chunk[-1]['end'],
                'words': current_chunk
            })
            current_chunk = []
    
    if current_chunk:
        chunk_text = ' '.join([w['word'] for w in current_chunk])
        chunks.append({
            'text': chunk_text,
            'start': current_chunk[0]['start'],
            'end': current_chunk[-1]['end'],
            'words': current_chunk
        })
    
    # Analyze each chunk
    sentiment_segments = []
    
    for chunk in chunks:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the sentiment and energy level. Return JSON with: sentiment (positive/neutral/negative), energy (0-10), engagement_score (0-10)"
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this text segment:\n\n{chunk['text']}"
                    }
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            import json
            content = response.choices[0].message.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(content)
            
            sentiment_segments.append({
                'start': chunk['start'],
                'end': chunk['end'],
                'sentiment': analysis.get('sentiment', 'neutral'),
                'energy': float(analysis.get('energy', 5)),
                'engagement_score': float(analysis.get('engagement_score', 5))
            })
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            continue
    
    return sentiment_segments


def detect_engagement_moments(sentiment_segments: List[Dict], threshold: float = 7.0) -> List[Dict]:
    """
    Identify high-engagement moments in the video.
    
    Args:
        sentiment_segments: List of sentiment analysis segments
        threshold: Minimum engagement score threshold
    
    Returns:
        List of high-engagement moments
    """
    high_engagement = []
    
    for segment in sentiment_segments:
        if segment['engagement_score'] >= threshold:
            high_engagement.append({
                'start': segment['start'],
                'end': segment['end'],
                'engagement_score': segment['engagement_score'],
                'energy': segment['energy'],
                'sentiment': segment['sentiment']
            })
    
    return high_engagement


def analyze_pacing(word_map: List[Dict]) -> Dict:
    """
    Analyze speech pacing and rhythm.
    
    Args:
        word_map: List of word dictionaries with timestamps
    
    Returns:
        Pacing analysis dictionary
    """
    if not word_map:
        return {}
    
    # Calculate word rate (words per minute)
    total_duration = word_map[-1]['end'] - word_map[0]['start']
    words_per_minute = (len(word_map) / total_duration) * 60
    
    # Calculate pause distribution
    pauses = []
    for i in range(len(word_map) - 1):
        pause_duration = word_map[i + 1]['start'] - word_map[i]['end']
        if pause_duration > 0:
            pauses.append(pause_duration)
    
    avg_pause = np.mean(pauses) if pauses else 0
    max_pause = max(pauses) if pauses else 0
    
    # Calculate speech rate variation
    segment_durations = []
    for i in range(0, len(word_map) - 10, 10):
        segment_duration = word_map[i + 9]['end'] - word_map[i]['start']
        segment_durations.append(segment_duration)
    
    pacing_variation = np.std(segment_durations) if segment_durations else 0
    
    return {
        'words_per_minute': words_per_minute,
        'average_pause_duration': avg_pause,
        'max_pause_duration': max_pause,
        'pacing_variation': pacing_variation,
        'pacing_score': calculate_pacing_score(words_per_minute, avg_pause)
    }


def calculate_pacing_score(wpm: float, avg_pause: float) -> float:
    """
    Calculate overall pacing score (0-10).
    Optimal: 150-180 WPM, 0.3-0.8s pauses
    """
    # WPM score (optimal around 165)
    wpm_score = 10 - abs(wpm - 165) / 16.5
    wpm_score = max(0, min(10, wpm_score))
    
    # Pause score (optimal 0.3-0.8s)
    if 0.3 <= avg_pause <= 0.8:
        pause_score = 10
    elif avg_pause < 0.3:
        pause_score = 10 - (0.3 - avg_pause) * 10
    else:
        pause_score = max(0, 10 - (avg_pause - 0.8) * 2)
    
    return (wpm_score + pause_score) / 2


def suggest_improvements(pacing_analysis: Dict, sentiment_segments: List[Dict]) -> List[str]:
    """
    Suggest improvements based on analysis.
    
    Args:
        pacing_analysis: Pacing analysis dictionary
        sentiment_segments: Sentiment segments
    
    Returns:
        List of improvement suggestions
    """
    suggestions = []
    
    wpm = pacing_analysis.get('words_per_minute', 0)
    avg_pause = pacing_analysis.get('average_pause_duration', 0)
    
    if wpm < 120:
        suggestions.append("Speech is too slow. Consider removing more pauses or speaking faster.")
    elif wpm > 200:
        suggestions.append("Speech is too fast. Consider adding more pauses for clarity.")
    
    if avg_pause > 1.5:
        suggestions.append("Too many long pauses detected. Remove silences to improve pacing.")
    elif avg_pause < 0.2:
        suggestions.append("Very few pauses. Consider adding brief pauses for better comprehension.")
    
    # Check for low engagement segments
    low_engagement_count = sum(1 for s in sentiment_segments if s['engagement_score'] < 5)
    if low_engagement_count > len(sentiment_segments) * 0.3:
        suggestions.append("Multiple low-engagement segments detected. Consider adding B-Roll or cutting these sections.")
    
    return suggestions

