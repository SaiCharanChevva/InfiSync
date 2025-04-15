import os
import subprocess
import tempfile
import sys
from pathlib import Path
import logging
import platform

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioExtractor:
    """
    Extracts audio from video files using ffmpeg.
    Handles ffmpeg path issues and provides robust audio extraction.
    """
    
    def __init__(self, temp_dir=None):
        """
        Initialize the AudioExtractor.
        
        Args:
            temp_dir: Optional directory to store temporary files. If None, system temp is used.
        """
        self.temp_dir = temp_dir if temp_dir else tempfile.mkdtemp()
        logger.info(f"Using temporary directory: {self.temp_dir}")
        
        # Find the FFMPEG path or use fallback methods
        self.ffmpeg_path = self._get_ffmpeg_path()
        
    def _get_ffmpeg_path(self):
        """
        Find the FFMPEG executable path, handling different OS and installation methods.
        
        Returns:
            Path to ffmpeg executable
        """
        # First, try the standard path
        if self._check_command("ffmpeg"):
            return "ffmpeg"
            
        # Check common installation locations based on OS
        system = platform.system()
        possible_paths = []
        
        if system == "Windows":
            possible_paths = [
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            ]
            # Also check if ffmpeg is in the current directory
            if os.path.exists("ffmpeg.exe"):
                possible_paths.append("./ffmpeg.exe")
                
        elif system == "Darwin":  # macOS
            possible_paths = [
                "/usr/local/bin/ffmpeg",
                "/opt/homebrew/bin/ffmpeg",
                "/opt/local/bin/ffmpeg",
            ]
            
        elif system == "Linux":
            possible_paths = [
                "/usr/bin/ffmpeg",
                "/usr/local/bin/ffmpeg",
                "/opt/ffmpeg/bin/ffmpeg",
            ]
            
        # Check each possible path
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"Found ffmpeg at: {path}")
                return path
                
        # If ffmpeg is not found, give instructions and raise an error
        self._handle_ffmpeg_not_found()
    
    def _check_command(self, command):
        """Check if a command is available in the system path."""
        try:
            subprocess.run([command, "-version"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=False)
            logger.info(f"Command '{command}' is available in system path")
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.info(f"Command '{command}' is not available in system path")
            return False
    
    def _handle_ffmpeg_not_found(self):
        """Handle the case when ffmpeg is not found."""
        system = platform.system()
        
        error_msg = "FFMPEG not found. "
        install_instructions = "\n\nInstallation instructions:\n"
        
        if system == "Windows":
            install_instructions += (
                "1. Download FFMPEG from https://ffmpeg.org/download.html\n"
                "2. Extract the downloaded ZIP file\n"
                "3. Add the 'bin' folder to your PATH environment variable\n"
                "   OR specify the full path to ffmpeg.exe when running this script\n"
            )
        elif system == "Darwin":  # macOS
            install_instructions += (
                "1. Install with Homebrew: brew install ffmpeg\n"
                "   OR\n"
                "2. Install with MacPorts: port install ffmpeg\n"
            )
        elif system == "Linux":
            install_instructions += (
                "For Ubuntu/Debian: sudo apt-get update && sudo apt-get install ffmpeg\n"
                "For Fedora: sudo dnf install ffmpeg\n"
                "For CentOS/RHEL: sudo yum install ffmpeg\n"
            )
            
        logger.error(error_msg + install_instructions)
        raise FileNotFoundError(error_msg + install_instructions)
            
    def extract_audio(self, video_path, output_path=None, format="wav"):
        """
        Extract audio from a video file.
        
        Args:
            video_path: Path to the video file
            output_path: Path where the audio file will be saved.
                         If None, a temporary file will be created.
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            Path to the extracted audio file
        """
        video_path = Path(video_path)
        
        # Check if video file exists
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        # Create output path if not provided
        if output_path is None:
            output_filename = f"{video_path.stem}_audio.{format}"
            output_path = Path(self.temp_dir) / output_filename
        else:
            output_path = Path(output_path)
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"Extracting audio from: {video_path}")
        logger.info(f"Output audio file: {output_path}")
        
        # Build the ffmpeg command
        command = [
            self.ffmpeg_path,
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le" if format == "wav" else "libmp3lame",
            "-ar", "16000",  # 16kHz sample rate (good for speech recognition)
            "-ac", "1",      # Mono (1 channel)
            "-y",            # Overwrite output file if it exists
            str(output_path)
        ]
        
        try:
            # Run the command
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            logger.info("Audio extraction completed successfully")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting audio: {e}")
            logger.error(f"FFMPEG stderr: {e.stderr}")
            
            # Check for specific errors
            if "No such file or directory" in e.stderr:
                raise FileNotFoundError(f"FFMPEG not found or not executable at: {self.ffmpeg_path}")
                
            raise RuntimeError(f"Failed to extract audio: {e.stderr}")


def main():
    """Main function to demonstrate usage of the AudioExtractor class."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract audio from video files")
    parser.add_argument("video_path", help="Path to the input video file")
    parser.add_argument("--output", help="Path to the output audio file (optional)")
    parser.add_argument("--format", choices=["wav", "mp3"], default="wav",
                       help="Output audio format (default: wav)")
    
    args = parser.parse_args()
    
    try:
        # Create an AudioExtractor instance
        extractor = AudioExtractor()
        
        # Extract audio
        output_path = extractor.extract_audio(
            video_path=args.video_path,
            output_path=args.output,
            format=args.format
        )
        
        print(f"\nAudio extraction completed successfully!")
        print(f"Audio saved to: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()