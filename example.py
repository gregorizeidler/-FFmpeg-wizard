"""
Example usage of FFmpeg Wizard Video Editor
"""

from video_editor import VideoEditor
from transcriber import transcribe_video
import os


def example_basic_editing():
    """Basic example: Remove silences and filler words."""
    input_video = "input_video.mp4"
    output_video = "output_basic.mp4"
    
    if not os.path.exists(input_video):
        print(f"Error: {input_video} not found. Please provide a video file.")
        return
    
    print("Example 1: Basic Editing (Remove Silences & Fillers)")
    print("=" * 60)
    
    with VideoEditor(input_video) as editor:
        # Process with basic features
        edited = editor.process_video(
            remove_silences=True,
            remove_fillers=True,
            apply_zoom=False,  # Disable zoom for this example
            insert_broll=False
        )
        
        editor.export_video(edited, output_video)
        print(f"\n✅ Output saved to: {output_video}")


def example_with_zoom():
    """Example with punch-in zoom effects."""
    input_video = "input_video.mp4"
    output_video = "output_zoom.mp4"
    
    if not os.path.exists(input_video):
        print(f"Error: {input_video} not found. Please provide a video file.")
        return
    
    print("\nExample 2: With Punch-in Zoom")
    print("=" * 60)
    
    with VideoEditor(input_video) as editor:
        edited = editor.process_video(
            remove_silences=True,
            remove_fillers=True,
            apply_zoom=True,  # Enable zoom
            insert_broll=False
        )
        
        editor.export_video(edited, output_video)
        print(f"\n✅ Output saved to: {output_video}")


def example_full_featured():
    """Full-featured example with B-Roll insertion."""
    input_video = "input_video.mp4"
    output_video = "output_full.mp4"
    
    if not os.path.exists(input_video):
        print(f"Error: {input_video} not found. Please provide a video file.")
        return
    
    print("\nExample 3: Full-Featured (All Features)")
    print("=" * 60)
    
    with VideoEditor(input_video) as editor:
        # Extract audio for transcription
        audio_path = editor.extract_audio()
        word_map = transcribe_video(audio_path)
        
        if word_map:
            transcript_text = " ".join([w['word'] for w in word_map])
            
            # Analyze for B-Roll (requires API keys)
            from broll_agent import analyze_context_for_broll, get_broll_videos
            
            try:
                suggestions = analyze_context_for_broll(word_map, transcript_text)
                broll_suggestions = get_broll_videos(suggestions)
                
                print(f"Found {len(broll_suggestions)} B-Roll suggestions")
            except Exception as e:
                print(f"B-Roll analysis failed: {e}")
                broll_suggestions = []
            
            # Process with all features
            edited = editor.process_video(
                remove_silences=True,
                remove_fillers=True,
                apply_zoom=True,
                insert_broll=len(broll_suggestions) > 0,
                broll_suggestions=broll_suggestions if broll_suggestions else None
            )
            
            editor.export_video(edited, output_video)
            print(f"\n✅ Output saved to: {output_video}")


if __name__ == "__main__":
    print("🎬 FFmpeg Wizard - Example Usage")
    print("=" * 60)
    print("\nChoose an example to run:")
    print("1. Basic editing (remove silences & fillers)")
    print("2. With punch-in zoom")
    print("3. Full-featured (all features including B-Roll)")
    print("\nNote: Make sure you have a video file named 'input_video.mp4'")
    print("      Or modify the script to use your video file path.")
    print("\nTo run a specific example, uncomment the function call below:")
    print()
    
    # Uncomment the example you want to run:
    # example_basic_editing()
    # example_with_zoom()
    # example_full_featured()

