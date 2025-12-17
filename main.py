"""
Command-line interface for FFmpeg Wizard Video Editor
"""

import argparse
import os
from video_editor import VideoEditor
from broll_agent import analyze_context_for_broll, get_broll_videos
from transcriber import transcribe_video


def main():
    parser = argparse.ArgumentParser(
        description="FFmpeg Wizard: AI-Powered Video Editor"
    )
    parser.add_argument(
        "input_video",
        help="Path to input video file"
    )
    parser.add_argument(
        "-o", "--output",
        default="output_edited.mp4",
        help="Output video file path (default: output_edited.mp4)"
    )
    parser.add_argument(
        "--no-silence-removal",
        action="store_true",
        help="Disable silence removal"
    )
    parser.add_argument(
        "--no-filler-removal",
        action="store_true",
        help="Disable filler word removal"
    )
    parser.add_argument(
        "--no-zoom",
        action="store_true",
        help="Disable punch-in zoom effects"
    )
    parser.add_argument(
        "--broll",
        action="store_true",
        help="Enable B-Roll video insertion"
    )
    parser.add_argument(
        "--min-silence",
        type=float,
        default=1.0,
        help="Minimum silence duration to cut (seconds, default: 1.0)"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_video):
        print(f"Error: Input file '{args.input_video}' not found.")
        return 1
    
    print("=" * 60)
    print("FFmpeg Wizard: AI-Powered Video Editor")
    print("=" * 60)
    print(f"Input: {args.input_video}")
    print(f"Output: {args.output}")
    print()
    
    try:
        with VideoEditor(args.input_video) as editor:
            # Extract audio and transcribe
            print("Step 1/5: Extracting audio...")
            audio_path = editor.extract_audio()
            
            print("Step 2/5: Transcribing video...")
            word_map = transcribe_video(audio_path)
            
            if not word_map:
                print("Error: Could not transcribe video. Please check if the video has audio.")
                return 1
            
            transcript_text = " ".join([w['word'] for w in word_map])
            print(f"✓ Transcribed {len(word_map)} words")
            
            # Analyze for B-Roll if enabled
            broll_suggestions = []
            if args.broll:
                print("Step 3/5: Analyzing content for B-Roll...")
                try:
                    suggestions = analyze_context_for_broll(word_map, transcript_text)
                    broll_suggestions = get_broll_videos(suggestions)
                    if broll_suggestions:
                        print(f"✓ Found {len(broll_suggestions)} B-Roll suggestions")
                except Exception as e:
                    print(f"Warning: B-Roll analysis failed: {e}")
                    args.broll = False
            
            # Process video
            print("Step 4/5: Processing video...")
            edited_video = editor.process_video(
                remove_silences=not args.no_silence_removal,
                remove_fillers=not args.no_filler_removal,
                apply_zoom=not args.no_zoom,
                insert_broll=args.broll,
                broll_suggestions=broll_suggestions if args.broll else None,
                min_silence_duration=args.min_silence
            )
            
            # Export
            print("Step 5/5: Rendering video...")
            editor.export_video(edited_video, args.output)
            
            # Show statistics
            original_duration = editor.video.duration
            edited_duration = edited_video.duration
            time_saved = original_duration - edited_duration
            
            print()
            print("=" * 60)
            print("Processing Complete!")
            print("=" * 60)
            print(f"Original duration: {original_duration:.1f}s")
            print(f"Edited duration: {edited_duration:.1f}s")
            print(f"Time saved: {time_saved:.1f}s ({time_saved/original_duration*100:.1f}%)")
            print(f"Output file: {args.output}")
            print("=" * 60)
            
            edited_video.close()
    
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

