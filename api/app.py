from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import tempfile
import logging
from pathlib import Path
import uuid
import threading
import json

# Import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from audio_extractor import AudioExtractor
import transcribe
import summarize
from entity_extractor import EntityExtractor
from audio_db import AudioProcessingDB

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enhanced CORS configuration
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
# CORS(app, resources={r"/api/*": {"origins": ["https://infysyncsummarizer.netlify.app/", "http://localhost:3000"]}}, supports_credentials=True)
#CORS(app, resources={r"/api/*": {"origins": ["https://meetingsummarizerinfysync.netlify.app/", "http://localhost:3000"]}}, supports_credentials=True)
# Add these headers to each response
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Create upload and results directories in /tmp for Render compatibility
# Or use the current directory if in development
if os.environ.get('RENDER'):
    # Use /tmp directory for Render deployment
    UPLOAD_FOLDER = '/tmp/uploads'
    RESULTS_FOLDER = '/tmp/results'
else:
    # Use local paths for development
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    RESULTS_FOLDER = os.path.join(os.path.dirname(__file__), 'results')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Database configuration - use environment variables for Render
DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "audio_processing"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "InfiSync25"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432")
}


# Initialize database connection - wrapped in a function to create a new connection for each thread
def get_db_connection():
    try:
        db = AudioProcessingDB(**DB_CONFIG)
        logger.info("Database connection established")
        return db
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

# Keep track of processing jobs
jobs = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    # Check database connection
    db = get_db_connection()
    if db:
        db.close()
        return jsonify({"status": "ok", "database": "connected"})
    else:
        return jsonify({"status": "ok", "database": "disconnected"})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle video file upload"""
    logger.info("Upload request received")
    
    if 'file' not in request.files:
        logger.error("No file part in request")
        return jsonify({"error": "No file part"}), 400
    
    logger.info(f"Request files: {list(request.files.keys())}")
    logger.info(f"Request form: {request.form or 'No form data'}")
    
    file = request.files['file']
    if file.filename == '':
        logger.error("No file selected")
        return jsonify({"error": "No file selected"}), 400
        
    # Generate a unique ID for this job
    job_id = str(uuid.uuid4())
    
    # Save the uploaded file
    filename = f"{job_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    logger.info(f"Saving file to {file_path}")
    file.save(file_path)
    
    # Check if file was saved successfully
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        logger.info(f"File saved successfully: {file_path} ({file_size} bytes)")
    else:
        logger.error(f"Failed to save file to {file_path}")
        return jsonify({"error": "Failed to save file"}), 500
    
    # Create job entry
    jobs[job_id] = {
        "status": "uploaded",
        "filename": file.filename,
        "file_path": file_path,
        "results": {},
        "db_ids": {}  # To store database IDs
    }
    
    logger.info(f"Started processing job {job_id} for file {file.filename}")
    
    return jsonify({
        "job_id": job_id,
        "status": "uploaded",
        "message": "File uploaded successfully"
    })

@app.route('/api/process/<job_id>', methods=['POST'])
def process_video(job_id):
    """Start processing a video file"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
        
    job = jobs[job_id]
    if job["status"] not in ["uploaded", "failed"]:
        return jsonify({"error": "File already being processed"}), 400
    
    # Update job status
    job["status"] = "processing"
    
    # Start processing in a separate thread
    thread = threading.Thread(target=process_job, args=(job_id,))
    thread.start()
    
    return jsonify({
        "job_id": job_id,
        "status": "processing",
        "message": "Processing started"
    })

def process_job(job_id):
    """Process a job in the background"""
    job = jobs[job_id]
    file_path = job["file_path"]
    results_path = os.path.join(RESULTS_FOLDER, job_id)
    os.makedirs(results_path, exist_ok=True)
    
    # Initialize database connection
    db = get_db_connection()
    
    try:
        # Step 1: Extract audio
        job["status"] = "extracting_audio"
        logger.info(f"Extracting audio for job {job_id}")
        extractor = AudioExtractor()
        
        # Save audio in the results folder for this job
        audio_output_path = os.path.join(results_path, "audio.wav")
        audio_path = extractor.extract_audio(
            video_path=file_path,
            output_path=audio_output_path,
            format="wav"
        )
        print("***********************audio extracted***********************")
        
        # Store the absolute path to the audio file
        job["results"]["audio_path"] = audio_path
        logger.info(f"Audio saved to {audio_path}")
        
        # Store audio in database if connection is available
        if db:
            try:
                audio_id = db.store_audio(audio_path, source="meeting")
                job["db_ids"]["audio_id"] = audio_id
                logger.info(f"Audio stored in database with ID: {audio_id}")
            except Exception as e:
                logger.error(f"Error storing audio in database: {str(e)}")
        
        # Step 2: Transcribe audio
        job["status"] = "transcribing"
        logger.info(f"Transcribing audio for job {job_id}")
        result = transcribe.transcribe_audio(audio_path, model_name="medium")
        formatted_transcript = transcribe.format_transcript(result)
        
        # Save transcript in the results folder
        transcript_path = os.path.join(results_path, "transcript.txt")
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(formatted_transcript)
        
        # Store the absolute path to the transcript file
        job["results"]["transcript_path"] = transcript_path
        logger.info(f"Transcript saved to {transcript_path}")
        logger.info(f"Transcription complete: {len(formatted_transcript)} characters")
        
        # Store transcription in database if connection is available
        if db and "audio_id" in job["db_ids"]:
            try:
                trans_id = db.store_transcription(
                    job["db_ids"]["audio_id"],
                    formatted_transcript,
                    language="en"
                )
                job["db_ids"]["transcription_id"] = trans_id
                logger.info(f"Transcription stored in database with ID: {trans_id}")
            except Exception as e:
                logger.error(f"Error storing transcription in database: {str(e)}")
        
        # Step 3: Extract entities and action items
        try:
            logger.info(f"Extracting entities and action items for job {job_id}")
            entity_extractor = EntityExtractor()
            extraction_results = entity_extractor.process_transcript(formatted_transcript)
            
            # Save extraction results in the results folder
            extraction_path = os.path.join(results_path, "extraction.json")
            with open(extraction_path, "w", encoding="utf-8") as f:
                json.dump(extraction_results, f, indent=2)
                
            job["results"]["extraction_path"] = extraction_path
            logger.info(f"Extraction results saved to {extraction_path}")
            
            # Store action items in database if connection is available
            if db and "audio_id" in job["db_ids"]:
                for item in extraction_results["action_items"]:
                    try:
                        action_id = db.store_action_item(
                            job["db_ids"]["audio_id"],
                            text=item["text"],
                            assignee=item.get("assignee", ""),
                            due_date=item.get("due_date", None),
                            priority="medium"  # Default priority
                        )
                        logger.info(f"Action item stored in database with ID: {action_id}")
                    except Exception as e:
                        logger.error(f"Error storing action item in database: {str(e)}")
        except Exception as e:
            logger.error(f"Error during entity extraction: {str(e)}")
            extraction_results = {"entities": {}, "action_items": []}
        
        # Step 4: Generate summary
        job["status"] = "summarizing"
        logger.info(f"Summarizing transcript for job {job_id}")
        
        try:
            # Use the TranscriptSummarizer class from your module
            summarizer = summarize.TranscriptSummarizer()
            
            # Generate formatted summary with entities and action items
            summary_text = summarizer.format_meeting_summary(
                formatted_transcript,
                extraction_results.get("entities", {}),
                extraction_results.get("action_items", [])
            )
            
        except Exception as summarize_error:
            # Fallback if summarization fails
            logger.error(f"Error during summarization: {str(summarize_error)}")
            logger.warning("Using fallback simple summary")
            summary_text = "# Meeting Summary\n\n"
            summary_text += "## Overview\n\n"
            summary_text += formatted_transcript[:500] + "...\n\n"
            summary_text += "*Full transcript available in the Transcript tab.*"
        
        # Save summary in the results folder
        summary_path = os.path.join(results_path, "summary.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_text)
        
        # Store the absolute path to the summary file
        job["results"]["summary_path"] = summary_path
        logger.info(f"Summary saved to {summary_path}")
        
        # Store summary in database if connection is available
        if db and "audio_id" in job["db_ids"]:
            try:
                summary_id = db.store_summary(job["db_ids"]["audio_id"], summary_text)
                job["db_ids"]["summary_id"] = summary_id
                logger.info(f"Summary stored in database with ID: {summary_id}")
            except Exception as e:
                logger.error(f"Error storing summary in database: {str(e)}")
        
        # Update job status
        job["status"] = "completed"
        logger.info(f"Completed job {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        job["status"] = "failed"
        job["error"] = str(e)
    finally:
        # Close database connection
        if db:
            db.close()
            logger.info("Database connection closed")

@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get the status of a processing job"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
        
    job = jobs[job_id]
    response = {
        "job_id": job_id,
        "status": job["status"],
        "filename": job["filename"]
    }
    
    if "error" in job:
        response["error"] = job["error"]
        
    # Include results paths if job is completed
    if job["status"] == "completed":
        response["results"] = {}
        # Use the correct URL paths, not filesystem paths
        response["results"]["audio"] = f"/api/results/{job_id}/audio"
        response["results"]["transcript"] = f"/api/results/{job_id}/transcript"
        response["results"]["summary"] = f"/api/results/{job_id}/summary"
        
        # Include database IDs if available
        if "db_ids" in job and job["db_ids"]:
            response["db_ids"] = job["db_ids"]
        
        # Log the response being sent for debugging
        logger.info(f"Sending completed job response: {response}")
    
    return jsonify(response)

@app.route('/api/results/<job_id>/audio', methods=['GET'])
def get_audio(job_id):
    """Get the extracted audio file"""
    if job_id not in jobs:
        logger.error(f"Audio not found: job {job_id} not found")
        return jsonify({"error": "Audio not found - job not found"}), 404
    
    job = jobs[job_id]
    
    # Check if we have an audio path
    if "results" not in job or "audio_path" not in job["results"]:
        logger.error(f"Audio not found for job {job_id}")
        return jsonify({"error": "Audio file not found"}), 404
    
    audio_path = job["results"]["audio_path"]
    logger.info(f"Serving audio file: {audio_path}")
    
    try:
        return send_file(audio_path, mimetype="audio/wav")
    except Exception as e:
        logger.error(f"Error serving audio file: {str(e)}")
        return jsonify({"error": f"Error serving audio file: {str(e)}"}), 500

@app.route('/api/results/<job_id>/transcript', methods=['GET'])
def get_transcript(job_id):
    """Get the transcript text"""
    if job_id not in jobs:
        logger.error(f"Transcript not found: job {job_id} not found")
        return jsonify({"error": "Transcript not found - job not found"}), 404
    
    job = jobs[job_id]
    
    # Check if we have a transcript path
    if "results" not in job or "transcript_path" not in job["results"]:
        logger.error(f"Transcript not found for job {job_id}")
        return jsonify({"error": "Transcript file not found"}), 404
    
    transcript_path = job["results"]["transcript_path"]
    logger.info(f"Reading transcript from: {transcript_path}")
    
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript = f.read()
        
        return jsonify({"transcript": transcript})
    except Exception as e:
        logger.error(f"Error reading transcript file: {str(e)}")
        return jsonify({"error": f"Error reading transcript file: {str(e)}"}), 500

@app.route('/api/results/<job_id>/summary', methods=['GET'])
def get_summary(job_id):
    """Get the summary text"""
    if job_id not in jobs:
        logger.error(f"Summary not found: job {job_id} not found")
        return jsonify({"error": "Summary not found - job not found"}), 404
    
    job = jobs[job_id]
    
    # Check if we have a summary path
    if "results" not in job or "summary_path" not in job["results"]:
        logger.error(f"Summary not found for job {job_id}")
        return jsonify({"error": "Summary file not found"}), 404
    
    summary_path = job["results"]["summary_path"]
    logger.info(f"Reading summary from: {summary_path}")
    
    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            summary_text = f.read()
        
        return jsonify({"summary": summary_text})
    except Exception as e:
        logger.error(f"Error reading summary file: {str(e)}")
        return jsonify({"error": f"Error reading summary file: {str(e)}"}), 500

@app.route('/api/results/<job_id>/extraction', methods=['GET'])
def get_extraction(job_id):
    """Get the entity extraction results"""
    if job_id not in jobs:
        logger.error(f"Extraction not found: job {job_id} not found")
        return jsonify({"error": "Extraction not found - job not found"}), 404
    
    job = jobs[job_id]
    
    # Check if we have an extraction path
    if "results" not in job or "extraction_path" not in job["results"]:
        logger.error(f"Extraction not found for job {job_id}")
        return jsonify({"error": "Extraction file not found"}), 404
    
    extraction_path = job["results"]["extraction_path"]
    logger.info(f"Reading extraction from: {extraction_path}")
    
    try:
        with open(extraction_path, "r", encoding="utf-8") as f:
            extraction_data = json.load(f)
        
        return jsonify(extraction_data)
    except Exception as e:
        logger.error(f"Error reading extraction file: {str(e)}")
        return jsonify({"error": f"Error reading extraction file: {str(e)}"}), 500

@app.route('/api/db/jobs', methods=['GET'])
def list_db_jobs():
    """List all jobs from the database"""
    db = get_db_connection()
    if not db:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        # Execute a SQL query to get all audio files with metadata
        db.cursor.execute("""
            SELECT id, filename, file_size, duration, recording_date, source, created_at
            FROM audio_files
            ORDER BY created_at DESC
        """)
        
        columns = ['id', 'filename', 'file_size', 'duration', 'recording_date', 'source', 'created_at']
        jobs_list = [dict(zip(columns, row)) for row in db.cursor.fetchall()]
        
        return jsonify({"jobs": jobs_list})
    except Exception as e:
        logger.error(f"Error fetching jobs from database: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/api/db/job/<audio_id>', methods=['GET'])
def get_db_job(audio_id):
    """Get job details from database by audio ID"""
    db = get_db_connection()
    if not db:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        # Get all processing data for this audio file
        result = db.get_audio_with_processed_data(audio_id)
        
        if not result:
            return jsonify({"error": "Job not found in database"}), 404
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching job from database: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs"""
    job_list = []
    for job_id, job in jobs.items():
        job_info = {
            "job_id": job_id,
            "status": job["status"],
            "filename": job["filename"],
            "created_at": job.get("created_at", "Unknown")
        }
        
        # Add database IDs if available
        if "db_ids" in job and job["db_ids"]:
            job_info["db_ids"] = job["db_ids"]
            
        job_list.append(job_info)
        
    return jsonify({"jobs": job_list})

if __name__ == '__main__':
    # Use PORT provided by Render environment variable
    port = int(os.environ.get('PORT', 5000))
    # Set debug to False in production
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
