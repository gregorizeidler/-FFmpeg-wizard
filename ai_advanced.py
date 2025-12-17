"""
Advanced AI Features Module
Script generation, speech improvement suggestions, repetition detection.
"""

from typing import List, Dict, Optional
import openai
import os
from dotenv import load_dotenv
from transcriber import transcribe_video
import re
from collections import Counter

load_dotenv()


class AdvancedAI:
    """Advanced AI-powered features."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def generate_script_from_topics(self, topics: List[str], style: str = "tutorial") -> str:
        """
        Generate video script from topics.
        
        Args:
            topics: List of topics to cover
            style: Script style ('tutorial', 'vlog', 'educational')
        
        Returns:
            Generated script
        """
        if not self.client:
            return "OpenAI API key required for script generation."
        
        topics_text = "\n".join([f"- {topic}" for topic in topics])
        
        prompt = f"""Generate a video script covering these topics:
{topics_text}

Style: {style}
Length: 3-5 minutes
Include natural transitions and engaging language.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional video script writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating script: {e}"
    
    def analyze_speech_quality(self, word_map: List[Dict], transcript_text: str) -> Dict:
        """
        Analyze speech quality and suggest improvements.
        
        Args:
            word_map: Word map from transcription
            transcript_text: Full transcript
        
        Returns:
            Analysis with suggestions
        """
        if not self.client:
            return {'error': 'OpenAI API key required'}
        
        # Detect repetitions
        repetitions = self.detect_repetitions(word_map)
        
        # Analyze clarity
        clarity_score = self.analyze_clarity(transcript_text)
        
        # Get AI suggestions
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a speech coach. Analyze speech and provide constructive feedback."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this transcript and suggest improvements:\n\n{transcript_text[:1000]}"
                    }
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            suggestions = response.choices[0].message.content.strip()
        except Exception as e:
            suggestions = f"Error analyzing: {e}"
        
        return {
            'repetitions': repetitions,
            'clarity_score': clarity_score,
            'suggestions': suggestions,
            'word_count': len(word_map),
            'filler_word_count': len([w for w in word_map if w['word'].lower() in ['um', 'uh', 'like', 'you know']])
        }
    
    def detect_repetitions(self, word_map: List[Dict], min_repeat: int = 2) -> List[Dict]:
        """
        Detect repeated phrases.
        
        Args:
            word_map: Word map
            min_repeat: Minimum repetitions to flag
        
        Returns:
            List of detected repetitions
        """
        # Extract phrases (2-4 words)
        phrases = []
        for i in range(len(word_map) - 3):
            phrase_words = [word_map[i+j]['word'].lower() for j in range(4)]
            phrase = ' '.join(phrase_words)
            phrases.append({
                'text': phrase,
                'start': word_map[i]['start'],
                'end': word_map[i+3]['end']
            })
        
        # Count phrase frequencies
        phrase_texts = [p['text'] for p in phrases]
        phrase_counts = Counter(phrase_texts)
        
        # Find repetitions
        repetitions = []
        seen_phrases = set()
        
        for phrase_data in phrases:
            phrase_text = phrase_data['text']
            count = phrase_counts[phrase_text]
            
            if count >= min_repeat and phrase_text not in seen_phrases:
                repetitions.append({
                    'phrase': phrase_text,
                    'count': count,
                    'first_occurrence': phrase_data['start'],
                    'suggestion': f"Consider removing or rephrasing: '{phrase_text}'"
                })
                seen_phrases.add(phrase_text)
        
        return repetitions
    
    def analyze_clarity(self, transcript_text: str) -> float:
        """
        Analyze speech clarity score (0-10).
        
        Args:
            transcript_text: Transcript text
        
        Returns:
            Clarity score
        """
        # Simple clarity metrics
        words = transcript_text.lower().split()
        
        # Check for filler words
        filler_words = ['um', 'uh', 'er', 'ah', 'like', 'you know', 'so', 'well']
        filler_count = sum(1 for word in words if word in filler_words)
        filler_ratio = filler_count / len(words) if words else 0
        
        # Check sentence length (very long sentences reduce clarity)
        sentences = re.split(r'[.!?]+', transcript_text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Calculate clarity score
        filler_penalty = min(filler_ratio * 3, 3)  # Max 3 point penalty
        length_penalty = max(0, (avg_sentence_length - 20) * 0.1)  # Penalty for very long sentences
        
        clarity_score = 10 - filler_penalty - length_penalty
        clarity_score = max(0, min(10, clarity_score))
        
        return clarity_score
    
    def suggest_improvements(self, transcript_text: str, word_map: List[Dict]) -> List[str]:
        """
        Generate improvement suggestions.
        
        Args:
            transcript_text: Transcript text
            word_map: Word map
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Analyze pacing
        if word_map:
            total_duration = word_map[-1]['end'] - word_map[0]['start']
            words_per_minute = (len(word_map) / total_duration * 60) if total_duration > 0 else 0
            
            if words_per_minute < 120:
                suggestions.append("Speech pace is slow. Consider speaking faster or removing more pauses.")
            elif words_per_minute > 200:
                suggestions.append("Speech pace is very fast. Consider slowing down for better comprehension.")
        
        # Check for filler words
        filler_words = ['um', 'uh', 'er', 'ah', 'like', 'you know']
        filler_count = sum(1 for w in word_map if w['word'].lower() in filler_words)
        if filler_count > len(word_map) * 0.05:  # More than 5% fillers
            suggestions.append(f"High number of filler words detected ({filler_count}). Consider removing them.")
        
        # Check for repetitions
        repetitions = self.detect_repetitions(word_map)
        if repetitions:
            suggestions.append(f"Found {len(repetitions)} repeated phrases. Consider rephrasing.")
        
        # Check clarity
        clarity = self.analyze_clarity(transcript_text)
        if clarity < 7:
            suggestions.append(f"Clarity score is {clarity:.1f}/10. Consider simplifying language or adding pauses.")
        
        return suggestions
    
    def enhance_transcript(self, transcript_text: str) -> str:
        """
        Enhance transcript with better word choices.
        
        Args:
            transcript_text: Original transcript
        
        Returns:
            Enhanced transcript
        """
        if not self.client:
            return transcript_text
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Improve the following transcript by removing filler words, fixing grammar, and making it more concise while maintaining the original meaning."
                    },
                    {
                        "role": "user",
                        "content": transcript_text
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error enhancing transcript: {e}"

