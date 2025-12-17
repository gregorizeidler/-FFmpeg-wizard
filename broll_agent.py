"""
B-Roll Agent Module
Uses LLM to analyze transcript and suggest B-Roll video insertions.
Integrates with Pexels API to fetch stock videos.
"""

import openai
import requests
import os
from typing import List, Dict, Optional
import json
from dotenv import load_dotenv

load_dotenv()


def get_pexels_video(query: str, duration: int = 5) -> Optional[str]:
    """
    Search for stock video on Pexels API.
    
    Args:
        query: Search query for the video
        duration: Desired duration in seconds
    
    Returns:
        URL to the video file or None if not found
    """
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("Warning: PEXELS_API_KEY not set. B-Roll feature disabled.")
        return None
    
    headers = {"Authorization": api_key}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation=landscape"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('videos'):
            video = data['videos'][0]
            # Get the best quality video file
            video_files = video.get('video_files', [])
            if video_files:
                # Prefer HD quality
                hd_files = [f for f in video_files if f.get('width', 0) >= 1280]
                if hd_files:
                    return hd_files[0]['link']
                return video_files[0]['link']
        
        return None
    except Exception as e:
        print(f"Error fetching Pexels video: {e}")
        return None


def analyze_context_for_broll(word_map: List[Dict], transcript_text: str) -> List[Dict]:
    """
    Use LLM to analyze transcript and suggest B-Roll insertion points.
    
    Args:
        word_map: List of word dictionaries with timestamps
        transcript_text: Full transcript text
    
    Returns:
        List of B-Roll suggestions with topic, timestamp, and duration
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not set. B-Roll analysis disabled.")
        return []
    
    client = openai.OpenAI(api_key=api_key)
    
    # Create a simplified prompt
    prompt = f"""Analyze the following video transcript and suggest where to insert B-Roll (stock footage) to make the video more engaging.

Transcript:
{transcript_text}

Return a JSON array of B-Roll suggestions. Each suggestion should have:
- "topic": A short search query for stock video (e.g., "Bitcoin cryptocurrency", "coding laptop")
- "timestamp_start": When to start the B-Roll (in seconds)
- "duration": How long the B-Roll should be (3-5 seconds)
- "reason": Why this B-Roll would be helpful

Only suggest 3-5 B-Roll insertions for the most important topics. Make sure timestamps don't overlap.

Return ONLY valid JSON, no other text:
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a video editing assistant. Return only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        # Sometimes LLM wraps JSON in markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        suggestions = json.loads(content)
        
        # Validate and filter suggestions
        valid_suggestions = []
        for suggestion in suggestions:
            if all(key in suggestion for key in ["topic", "timestamp_start", "duration"]):
                valid_suggestions.append(suggestion)
        
        return valid_suggestions
        
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response as JSON: {e}")
        return []
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return []


def get_broll_videos(suggestions: List[Dict]) -> List[Dict]:
    """
    Fetch B-Roll videos from Pexels based on LLM suggestions.
    
    Args:
        suggestions: List of B-Roll suggestions from LLM
    
    Returns:
        List of B-Roll dictionaries with video URLs
    """
    broll_videos = []
    
    for suggestion in suggestions:
        topic = suggestion.get("topic", "")
        video_url = get_pexels_video(topic, duration=suggestion.get("duration", 5))
        
        if video_url:
            broll_videos.append({
                **suggestion,
                "video_url": video_url
            })
        else:
            print(f"Could not find B-Roll video for topic: {topic}")
    
    return broll_videos

