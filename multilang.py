"""
Multi-Language Support Module
Transcription in multiple languages, translation, TTS dubbing.
"""

from typing import List, Dict, Optional
from transcriber import transcribe_video
from faster_whisper import WhisperModel
import openai
import os
from dotenv import load_dotenv

load_dotenv()


class MultiLanguageProcessor:
    """Handles multi-language transcription and translation."""
    
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi'
        }
    
    def detect_language(self, audio_path: str) -> str:
        """
        Detect language of audio.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Language code
        """
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path, beam_size=5)
        
        detected_language = info.language
        return detected_language
    
    def transcribe_in_language(
        self,
        audio_path: str,
        language: Optional[str] = None,
        model_size: str = "small"
    ) -> List[Dict]:
        """
        Transcribe audio in specific language.
        
        Args:
            audio_path: Path to audio file
            language: Language code (None for auto-detect)
            model_size: Whisper model size
        
        Returns:
            List of word dictionaries with timestamps
        """
        device = os.getenv("WHISPER_DEVICE", "cpu")
        compute_type = "int8" if device == "cpu" else "float16"
        
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        
        if language:
            segments, info = model.transcribe(
                audio_path,
                language=language,
                beam_size=5,
                word_timestamps=True
            )
        else:
            segments, info = model.transcribe(
                audio_path,
                beam_size=5,
                word_timestamps=True
            )
        
        word_map = []
        for segment in segments:
            for word in segment.words:
                word_map.append({
                    "word": word.word.strip(),
                    "start": word.start,
                    "end": word.end,
                    "confidence": word.probability,
                    "language": info.language
                })
        
        return word_map
    
    def translate_transcript(
        self,
        word_map: List[Dict],
        target_language: str
    ) -> List[Dict]:
        """
        Translate transcript to target language.
        
        Args:
            word_map: Original word map
            target_language: Target language code
        
        Returns:
            Translated word map
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OpenAI API key required for translation")
            return word_map
        
        client = openai.OpenAI(api_key=api_key)
        
        # Group words into sentences for better translation
        transcript_text = " ".join([w['word'] for w in word_map])
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator. Translate the following text to {self.supported_languages.get(target_language, target_language)}. Maintain the same structure and meaning."
                    },
                    {
                        "role": "user",
                        "content": transcript_text
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Split translated text back into words (simplified)
            # In production, use proper word alignment
            translated_words = translated_text.split()
            
            # Map translated words back to timestamps
            translated_map = []
            words_per_segment = len(translated_words) / len(word_map) if word_map else 1
            
            for i, original_word in enumerate(word_map):
                word_idx = int(i * words_per_segment)
                if word_idx < len(translated_words):
                    translated_map.append({
                        **original_word,
                        "word": translated_words[word_idx],
                        "original_word": original_word["word"],
                        "language": target_language
                    })
                else:
                    translated_map.append({
                        **original_word,
                        "language": target_language
                    })
            
            return translated_map
            
        except Exception as e:
            print(f"Error translating: {e}")
            return word_map
    
    def generate_subtitles_multilang(
        self,
        audio_path: str,
        languages: List[str],
        output_dir: str
    ) -> Dict[str, str]:
        """
        Generate subtitles in multiple languages.
        
        Args:
            audio_path: Path to audio file
            languages: List of language codes
            output_dir: Output directory
        
        Returns:
            Dictionary mapping language codes to subtitle file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Detect original language
        original_language = self.detect_language(audio_path)
        
        # Transcribe in original language
        original_word_map = self.transcribe_in_language(audio_path, original_language)
        
        subtitle_files = {}
        
        # Generate subtitles for each language
        for lang in languages:
            if lang == original_language:
                word_map = original_word_map
            else:
                word_map = self.translate_transcript(original_word_map, lang)
            
            # Generate subtitle file
            from subtitles import generate_srt, generate_vtt
            
            srt_path = os.path.join(output_dir, f"subtitles_{lang}.srt")
            generate_srt(word_map, srt_path)
            subtitle_files[lang] = srt_path
        
        return subtitle_files
    
    def create_dubbed_audio(
        self,
        transcript_text: str,
        target_language: str,
        output_path: str,
        voice: str = "alloy"
    ) -> str:
        """
        Create dubbed audio using TTS.
        
        Args:
            transcript_text: Transcript text
            target_language: Target language code
            output_path: Output audio path
            voice: TTS voice name
        
        Returns:
            Output audio path
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OpenAI API key required for TTS")
            return None
        
        client = openai.OpenAI(api_key=api_key)
        
        try:
            # Translate if needed
            if target_language != 'en':
                translated = self.translate_transcript(
                    [{'word': w} for w in transcript_text.split()],
                    target_language
                )
                text_to_speak = " ".join([w.get('word', w.get('original_word', '')) for w in translated])
            else:
                text_to_speak = transcript_text
            
            # Generate speech
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text_to_speak
            )
            
            # Save audio
            response.stream_to_file(output_path)
            
            return output_path
            
        except Exception as e:
            print(f"Error creating dubbed audio: {e}")
            return None

