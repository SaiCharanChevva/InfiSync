import os
import argparse
from pathlib import Path
import logging
from audio_extractor import AudioExtractor

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Extract audio from a meeting video file.
    This is the first step in the meeting summarization pipeline.
    """
    parser = argparse.ArgumentParser(description="Extract audio from meeting videos")
    
    parser.add_argument(
        "video_path",
        help="Path to the meeting video file"
    )
    
    parser.add_argument(
        "--output",
        help="Path to save the extracted audio (optional)"
    )
    
    parser.add_argument(
        "--format",
        choices=["wav", "mp3"],
        default="wav",
        help="Output audio format (default: wav)"
    )
    
    args = parser.parse_args()
    
    # Create output directory if needed
    if args.output:
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    try:
        # Initialize the audio extractor
        extractor = AudioExtractor()
        
        # Extract audio from the video
        output_path = extractor.extract_audio(
            video_path=args.video_path,
            output_path=args.output,
            format=args.format
        )
        
        print(f"\nAudio extraction completed successfully!")
        print(f"Audio saved to: {output_path}")
        print("\nNext steps in the pipeline:")
        print("1. Extract audio from video")
        print("2. Transcribe audio using Whisper")
        print("3. Summarize transcript using BART")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())