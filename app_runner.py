import os
import argparse
import logging
from datetime import datetime
import uuid

# Import our modules
from audio_extractor import AudioExtractor
import transcribe
import summarize
from entity_extractor import EntityExtractor
from audio_db import AudioProcessingDB

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_meeting_recording(video_path, output_dir=None, db_config=None):
    """
    Process a meeting recording through the entire pipeline:
    1. Extract audio
    2. Transcribe audio
    3. Extract entities and action items
    4. Summarize content
    5. Store everything in the database
    
    Args:
        video_path: Path to the meeting video file
        output_dir: Directory to save output files (optional)
        db_config: Database configuration dictionary (optional)
        
    Returns:
        Dictionary with processing results and file paths
    """
    # Create output directory if it doesn't exist
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    # Initialize database connection if config provided
    db = None
    if db_config:
        db = AudioProcessingDB(
            dbname=db_config.get("dbname", "audio_processing"),
            user=db_config.get("user", "postgres"),
            password=db_config.get("password", "Liyansh2820"),
            host=db_config.get("host", "localhost"),
            port=db_config.get("port", "5432")
        )
        logger.info("Database connection established")
    
    try:
        # Step 1: Extract audio from video
        logger.info(f"Extracting audio from {video_path}")
        extractor = AudioExtractor()
        if output_dir:
            audio_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_audio.wav"
            audio_path = os.path.join(output_dir, audio_filename)
        else:
            audio_path = None
            
        audio_path = extractor.extract_audio(
            video_path=video_path,
            output_path=audio_path,
            format="wav"
        )
        logger.info(f"Audio extracted to {audio_path}")
        
        # Store audio in database if available
        audio_id = None
        if db:
            audio_id = db.store_audio(audio_path, source="meeting")
            logger.info(f"Audio stored in database with ID: {audio_id}")
        
        # Step 2: Transcribe audio
        logger.info(f"Transcribing audio: {audio_path}")
        transcription_result = transcribe.transcribe_audio(audio_path, model_name="turbo")
        formatted_transcript = transcribe.format_transcript(transcription_result)
        
        if output_dir:
            transcript_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}_transcript.txt")
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(formatted_transcript)
            logger.info(f"Transcript saved to {transcript_path}")
        
        # Store transcription in database if available
        if db and audio_id:
            trans_id = db.store_transcription(
                audio_id, 
                formatted_transcript, 
                language=transcription_result.get("language", "en")
            )
            logger.info(f"Transcription stored in database with ID: {trans_id}")
        
        # Step 3: Extract entities and action items
        logger.info("Extracting entities and action items")
        entity_extractor = EntityExtractor()
        extraction_results = entity_extractor.process_transcript(formatted_transcript)
        
        if output_dir:
            extraction_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}_extraction.json")
            entity_extractor.save_results(extraction_results, extraction_path)
            logger.info(f"Extraction results saved to {extraction_path}")
        
        # Step 4: Generate summary
        logger.info("Generating meeting summary")
        summarizer = summarize.TranscriptSummarizer()
        meeting_summary = summarizer.format_meeting_summary(
            formatted_transcript,
            extraction_results["entities"],
            extraction_results["action_items"]
        )
        
        if output_dir:
            summary_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}_summary.md")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(meeting_summary)
            logger.info(f"Summary saved to {summary_path}")
        
        # Store summary in database if available
        if db and audio_id:
            summary_id = db.store_summary(audio_id, meeting_summary)
            logger.info(f"Summary stored in database with ID: {summary_id}")
            
            # Store action items
            for item in extraction_results["action_items"]:
                action_id = db.store_action_item(
                    audio_id,
                    text=item["text"],
                    assignee=item.get("assignee", ""),
                    due_date=item.get("due_date", None),
                    priority="medium"  # Default priority
                )
                logger.info(f"Action item stored in database with ID: {action_id}")
        
        # Return results
        results = {
            "audio_path": audio_path,
            "transcript": formatted_transcript,
            "entities": extraction_results["entities"],
            "action_items": extraction_results["action_items"],
            "summary": meeting_summary
        }
        
        if db and audio_id:
            results["audio_id"] = audio_id
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing meeting recording: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Close database connection if open
        if db:
            db.close()
            logger.info("Database connection closed")

def main():
    """Main function to process meeting recordings"""
    parser = argparse.ArgumentParser(description="Process meeting recordings")
    
    parser.add_argument(
        "video_path",
        help="Path to the meeting video file"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Directory to save output files (optional)"
    )
    
    parser.add_argument(
        "--use-db",
        action="store_true",
        help="Store results in PostgreSQL database"
    )
    
    parser.add_argument(
        "--db-user",
        default="postgres",
        help="PostgreSQL username"
    )
    
    parser.add_argument(
        "--db-password",
        help="PostgreSQL password"
    )
    
    parser.add_argument(
        "--db-host",
        default="localhost",
        help="PostgreSQL host"
    )
    
    parser.add_argument(
        "--db-port",
        default="5432",
        help="PostgreSQL port"
    )
    
    parser.add_argument(
        "--db-name",
        default="audio_processing",
        help="PostgreSQL database name"
    )
    
    args = parser.parse_args()
    
    # Set up database configuration if needed
    db_config = None
    if args.use_db:
        if not args.db_password:
            import getpass
            password = getpass.getpass("Enter PostgreSQL password: ")
        else:
            password = args.db_password
            
        db_config = {
            "dbname": args.db_name,
            "user": args.db_user,
            "password": password,
            "host": args.db_host,
            "port": args.db_port
        }
    
    try:
        # Process the meeting recording
        results = process_meeting_recording(
            video_path=args.video_path,
            output_dir=args.output_dir,
            db_config=db_config
        )
        
        # Print summary of results
        print("\n" + "="*80)
        print("PROCESSING SUMMARY")
        print("="*80)
        print(f"Video: {args.video_path}")
        print(f"Audio: {results['audio_path']}")
        
        if args.output_dir:
            print(f"Output directory: {args.output_dir}")
            
        print(f"Entities extracted: {sum(len(entities) for entities in results['entities'].values())}")
        print(f"Action items found: {len(results['action_items'])}")
        
        if args.use_db:
            print(f"All results stored in database (Audio ID: {results.get('audio_id')})")
            
        print("="*80)
        print("Processing completed successfully!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())