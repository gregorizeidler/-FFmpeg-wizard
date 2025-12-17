"""
Performance Analysis Module
Detailed statistics and before/after comparisons.
"""

from typing import Dict, List
from datetime import datetime
import json
import os
from moviepy.editor import VideoFileClip


class PerformanceAnalyzer:
    """Analyzes video editing performance and statistics."""
    
    def __init__(self):
        self.stats_history = []
    
    def analyze_editing_session(
        self,
        original_video_path: str,
        edited_video_path: str,
        word_map: List[Dict],
        editing_settings: Dict
    ) -> Dict:
        """
        Analyze editing session and generate statistics.
        
        Args:
            original_video_path: Original video path
            edited_video_path: Edited video path
            word_map: Word map from transcription
            editing_settings: Settings used for editing
        
        Returns:
            Analysis dictionary
        """
        original_clip = VideoFileClip(original_video_path)
        edited_clip = VideoFileClip(edited_video_path)
        
        original_duration = original_clip.duration
        edited_duration = edited_clip.duration
        
        # Calculate time saved
        time_saved = original_duration - edited_duration
        time_saved_percent = (time_saved / original_duration * 100) if original_duration > 0 else 0
        
        # Count words
        total_words = len(word_map)
        
        # Count removed segments
        silence_gaps = []
        for i in range(len(word_map) - 1):
            gap = word_map[i + 1]['start'] - word_map[i]['end']
            if gap > editing_settings.get('min_silence_duration', 1.0):
                silence_gaps.append(gap)
        
        total_silence_removed = sum(silence_gaps)
        
        # File size comparison
        original_size = os.path.getsize(original_video_path) / (1024 * 1024)  # MB
        edited_size = os.path.getsize(edited_video_path) / (1024 * 1024)  # MB
        size_reduction = ((original_size - edited_size) / original_size * 100) if original_size > 0 else 0
        
        # Calculate words per minute
        words_per_minute_original = (total_words / original_duration * 60) if original_duration > 0 else 0
        words_per_minute_edited = (total_words / edited_duration * 60) if edited_duration > 0 else 0
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'original': {
                'duration': original_duration,
                'file_size_mb': original_size,
                'words_count': total_words,
                'words_per_minute': words_per_minute_original
            },
            'edited': {
                'duration': edited_duration,
                'file_size_mb': edited_size,
                'words_count': total_words,
                'words_per_minute': words_per_minute_edited
            },
            'improvements': {
                'time_saved_seconds': time_saved,
                'time_saved_percent': time_saved_percent,
                'silence_removed_seconds': total_silence_removed,
                'silence_gaps_removed': len(silence_gaps),
                'size_reduction_mb': original_size - edited_size,
                'size_reduction_percent': size_reduction,
                'pacing_improvement': words_per_minute_edited - words_per_minute_original
            },
            'settings_used': editing_settings
        }
        
        original_clip.close()
        edited_clip.close()
        
        # Save to history
        self.stats_history.append(analysis)
        
        return analysis
    
    def generate_report(self, analysis: Dict) -> str:
        """
        Generate human-readable report.
        
        Args:
            analysis: Analysis dictionary
        
        Returns:
            Report string
        """
        report = []
        report.append("=" * 60)
        report.append("VIDEO EDITING PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append("")
        
        report.append("ORIGINAL VIDEO:")
        report.append(f"  Duration: {analysis['original']['duration']:.2f} seconds")
        report.append(f"  File Size: {analysis['original']['file_size_mb']:.2f} MB")
        report.append(f"  Words: {analysis['original']['words_count']}")
        report.append(f"  Words/Minute: {analysis['original']['words_per_minute']:.1f}")
        report.append("")
        
        report.append("EDITED VIDEO:")
        report.append(f"  Duration: {analysis['edited']['duration']:.2f} seconds")
        report.append(f"  File Size: {analysis['edited']['file_size_mb']:.2f} MB")
        report.append(f"  Words: {analysis['edited']['words_count']}")
        report.append(f"  Words/Minute: {analysis['edited']['words_per_minute']:.1f}")
        report.append("")
        
        report.append("IMPROVEMENTS:")
        report.append(f"  Time Saved: {analysis['improvements']['time_saved_seconds']:.2f} seconds ({analysis['improvements']['time_saved_percent']:.1f}%)")
        report.append(f"  Silence Removed: {analysis['improvements']['silence_removed_seconds']:.2f} seconds")
        report.append(f"  Silence Gaps Removed: {analysis['improvements']['silence_gaps_removed']}")
        report.append(f"  Size Reduction: {analysis['improvements']['size_reduction_mb']:.2f} MB ({analysis['improvements']['size_reduction_percent']:.1f}%)")
        report.append(f"  Pacing Improvement: {analysis['improvements']['pacing_improvement']:+.1f} WPM")
        report.append("")
        
        report.append("SETTINGS USED:")
        for key, value in analysis['settings_used'].items():
            report.append(f"  {key}: {value}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_history(self, file_path: str = "editing_history.json"):
        """Save editing history to file."""
        with open(file_path, 'w') as f:
            json.dump(self.stats_history, f, indent=2)
    
    def load_history(self, file_path: str = "editing_history.json"):
        """Load editing history from file."""
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                self.stats_history = json.load(f)
    
    def get_average_stats(self) -> Dict:
        """Get average statistics across all sessions."""
        if not self.stats_history:
            return {}
        
        total_sessions = len(self.stats_history)
        
        avg_time_saved = sum(s['improvements']['time_saved_percent'] for s in self.stats_history) / total_sessions
        avg_size_reduction = sum(s['improvements']['size_reduction_percent'] for s in self.stats_history) / total_sessions
        
        return {
            'total_sessions': total_sessions,
            'average_time_saved_percent': avg_time_saved,
            'average_size_reduction_percent': avg_size_reduction
        }

