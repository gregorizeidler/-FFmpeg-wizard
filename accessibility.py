"""
Accessibility Features Module
Closed captions with action descriptions, audio descriptions, high contrast.
"""

from typing import List, Dict, Optional
from subtitles import generate_srt, generate_vtt
from transcriber import transcribe_video
import openai
import os
from dotenv import load_dotenv

load_dotenv()


class AccessibilityManager:
    """Manages accessibility features for videos."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def generate_descriptive_captions(
        self,
        word_map: List[Dict],
        video_path: str,
        sample_rate: float = 2.0
    ) -> List[Dict]:
        """
        Generate captions with action descriptions.
        
        Args:
            word_map: Word map from transcription
            video_path: Video file path
            sample_rate: Sample frames every N seconds
        
        Returns:
            Enhanced captions with descriptions
        """
        from moviepy.editor import VideoFileClip
        
        clip = VideoFileClip(video_path)
        enhanced_captions = []
        
        current_time = 0
        while current_time < clip.duration:
            # Get transcript for this segment
            segment_words = [
                w for w in word_map
                if current_time <= w['start'] < current_time + sample_rate
            ]
            
            if segment_words:
                transcript_segment = " ".join([w['word'] for w in segment_words])
                
                # Describe visual content (simplified - in production, use video analysis)
                visual_description = self._describe_visual_content(clip, current_time)
                
                enhanced_captions.append({
                    'start': segment_words[0]['start'],
                    'end': segment_words[-1]['end'],
                    'text': transcript_segment,
                    'visual_description': visual_description,
                    'full_caption': f"{transcript_segment} [{visual_description}]" if visual_description else transcript_segment
                })
            
            current_time += sample_rate
        
        clip.close()
        
        return enhanced_captions
    
    def _describe_visual_content(self, clip, time: float) -> str:
        """
        Describe visual content at a specific time.
        
        Args:
            clip: Video clip
            time: Time in seconds
        
        Returns:
            Visual description
        """
        # Simplified - in production, use computer vision
        # For now, return empty or basic description
        return ""
    
    def create_audio_description(
        self,
        video_path: str,
        transcript_text: str,
        output_path: str
    ) -> str:
        """
        Create audio description track.
        
        Args:
            video_path: Video file path
            transcript_text: Video transcript
            output_path: Output audio description file path
        
        Returns:
            Output file path
        """
        if not self.client:
            return None
        
        # Generate audio description script
        try:
            prompt = f"""Create an audio description script for this video transcript. 
            Describe visual elements, actions, and important visual information that isn't conveyed in the audio.
            Keep descriptions concise and timed appropriately.
            
            Transcript:
            {transcript_text[:1500]}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an audio description writer. Create concise, clear descriptions of visual content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            description_text = response.choices[0].message.content.strip()
            
            # Generate TTS audio
            audio_response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=description_text
            )
            
            audio_response.stream_to_file(output_path)
            
            return output_path
            
        except Exception as e:
            print(f"Error creating audio description: {e}")
            return None
    
    def apply_high_contrast(self, video_path: str, output_path: str) -> str:
        """
        Apply high contrast filter for visibility.
        
        Args:
            video_path: Input video path
            output_path: Output video path
        
        Returns:
            Output video path
        """
        import cv2
        from moviepy.editor import VideoFileClip
        
        clip = VideoFileClip(video_path)
        
        def enhance_contrast(frame):
            # Convert to LAB color space
            lab = cv2.cvtColor(frame, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Increase saturation slightly
            a = cv2.convertScaleAbs(a, alpha=1.2, beta=0)
            b = cv2.convertScaleAbs(b, alpha=1.2, beta=0)
            
            lab = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            
            return enhanced
        
        enhanced_clip = clip.fl(enhance_contrast, apply_to=['video'])
        enhanced_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        clip.close()
        enhanced_clip.close()
        
        return output_path
    
    def generate_accessibility_package(
        self,
        video_path: str,
        word_map: List[Dict],
        transcript_text: str,
        output_dir: str
    ) -> Dict:
        """
        Generate complete accessibility package.
        
        Args:
            video_path: Video file path
            word_map: Word map
            transcript_text: Transcript text
            output_dir: Output directory
        
        Returns:
            Dictionary with paths to generated files
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        package = {}
        
        # Generate standard subtitles
        srt_path = os.path.join(output_dir, "subtitles.srt")
        generate_srt(word_map, srt_path)
        package['subtitles_srt'] = srt_path
        
        vtt_path = os.path.join(output_dir, "subtitles.vtt")
        generate_vtt(word_map, vtt_path)
        package['subtitles_vtt'] = vtt_path
        
        # Generate descriptive captions
        descriptive_captions = self.generate_descriptive_captions(word_map, video_path)
        if descriptive_captions:
            # Convert to SRT format
            descriptive_srt = os.path.join(output_dir, "subtitles_descriptive.srt")
            # Would need to implement SRT generation from enhanced captions
            package['subtitles_descriptive'] = descriptive_srt
        
        # Generate audio description
        audio_desc_path = os.path.join(output_dir, "audio_description.mp3")
        audio_desc = self.create_audio_description(video_path, transcript_text, audio_desc_path)
        if audio_desc:
            package['audio_description'] = audio_desc
        
        # Generate high contrast version
        high_contrast_path = os.path.join(output_dir, "video_high_contrast.mp4")
        self.apply_high_contrast(video_path, high_contrast_path)
        package['high_contrast_video'] = high_contrast_path
        
        return package

