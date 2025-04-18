import os
import argparse
import whisper
from typing import Optional

def transcribe_audio(audio_path: str, model_name: str = "small", language: Optional[str] = None) -> dict:
    """
    Transcribe an audio file using OpenAI's Whisper model.
    
    Args:
        audio_path: Path to the audio file
        model_name: Whisper model to use (tiny, base, small, medium, large, turbo)
        language: Optional language code (auto-detects if not provided)
        
    Returns:
        Transcription result dictionary
    """
    print(f"Loading Whisper model: {model_name}")
    model = whisper.load_model(model_name)
    
    print(f"Transcribing audio file: {audio_path}")
    
    # Set transcription options
    options = {}
    if language:
        options["language"] = language
        
    # Perform the transcription
    result = model.transcribe(audio_path, **options)
    
    print(f"Transcription completed. Found {len(result['segments'])} segments.")
    return result

def format_transcript(result: dict) -> str:
    """
    Format the transcription result into a readable format with timestamps.
    
    Args:
        result: Transcription result from Whisper
        
    Returns:
        Formatted transcript as a string
    """
    # Get the full text
    transcript = result["text"]
    
    # Add segment timestamps
    detailed_transcript = []
    for segment in result["segments"]:
        start = format_time(segment["start"])
        end = format_time(segment["end"])
        detailed_transcript.append(f"[{start} - {end}] {segment['text']}")
    
    # Join the segments
    formatted_transcript = "\n".join(detailed_transcript)
    
    return formatted_transcript

def format_time(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

def main():
    parser = argparse.ArgumentParser(description="Audio Transcription with Whisper")
    parser.add_argument("audio_path", help="Path to the audio file")
    parser.add_argument("--model", default="small", 
                      help="Whisper model to use (tiny, base, small, medium, large)")
    parser.add_argument("--language", help="Language code (optional, auto-detects if not specified)")
    parser.add_argument("--output", help="Output file path (optional)")
    
    args = parser.parse_args()
    
    # Ensure the audio file exists
    if not os.path.exists(args.audio_path):
        print(f"Error: Audio file not found: {args.audio_path}")
        return
    
    try:
        # Transcribe the audio
        result = transcribe_audio(args.audio_path, args.model, args.language)
        
        # Format the transcript
        formatted_transcript = format_transcript(result)
        
        # Output the transcript
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(formatted_transcript)
            print(f"Transcript saved to {args.output}")
        else:
            print("\n" + "="*80 + "\n")
            print("TRANSCRIPT:")
            print(formatted_transcript)
            print("\n" + "="*80)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
