import os
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime
import uuid
import logging

# Set up logging
logger = logging.getLogger(__name__)

class AudioProcessingDB:
    def __init__(self, dbname=None, user=None, password=None, host=None, port=None, url=None):
        """Initialize the database connection using parameters or a DATABASE_URL."""
        # Check if DATABASE_URL environment variable exists (provided by Render)
        database_url = url or os.environ.get("DATABASE_URL")
        
        if database_url:
            # Use the DATABASE_URL (Render format)
            logger.info("Connecting to database using DATABASE_URL")
            self.conn = psycopg2.connect(database_url)
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
        else:
            # Use individual parameters with environment variable fallbacks
            self.conn_params = {
                "dbname": dbname or os.environ.get("DB_NAME", "audio_processing"),
                "user": user or os.environ.get("DB_USER", "postgres"),
                "password": password or os.environ.get("DB_PASSWORD", "InfiSync25"),
                "host": host or os.environ.get("DB_HOST", "localhost"),
                "port": port or os.environ.get("DB_PORT", "5432")
            }
            
            # Try to connect to the database, create it if it doesn't exist
            try:
                logger.info(f"Connecting to database {self.conn_params['dbname']} on {self.conn_params['host']}")
                self.conn = psycopg2.connect(**self.conn_params)
                self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                self.cursor = self.conn.cursor()
            except psycopg2.OperationalError as e:
                logger.warning(f"Error connecting to database: {str(e)}")
                logger.info("Attempting to create database...")
                
                # Connect to default postgres database to create our database
                try:
                    temp_params = self.conn_params.copy()
                    temp_params["dbname"] = "postgres"
                    conn = psycopg2.connect(**temp_params)
                    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                    cursor = conn.cursor()
                    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.conn_params["dbname"])))
                    cursor.close()
                    conn.close()
                    
                    # Now connect to our newly created database
                    self.conn = psycopg2.connect(**self.conn_params)
                    self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                    self.cursor = self.conn.cursor()
                    logger.info(f"Successfully created and connected to database {self.conn_params['dbname']}")
                except Exception as create_error:
                    logger.error(f"Failed to create database: {str(create_error)}")
                    raise
        
        # Create tables if they don't exist
        self._create_tables()
    
    def _create_tables(self):
        """Create the necessary tables if they don't exist."""
        logger.info("Creating tables if they don't exist")
        
        # Create audio_files table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS audio_files (
                id UUID PRIMARY KEY,
                filename TEXT NOT NULL,
                file_data BYTEA NOT NULL,
                file_size BIGINT NOT NULL,
                duration FLOAT,
                format TEXT,
                recording_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create transcriptions table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcriptions (
                id UUID PRIMARY KEY,
                audio_id UUID REFERENCES audio_files(id) ON DELETE CASCADE,
                text TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                confidence FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create summaries table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id UUID PRIMARY KEY,
                audio_id UUID REFERENCES audio_files(id) ON DELETE CASCADE,
                text TEXT NOT NULL,
                version TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create action_items table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_items (
                id UUID PRIMARY KEY,
                audio_id UUID REFERENCES audio_files(id) ON DELETE CASCADE,
                text TEXT NOT NULL,
                priority TEXT,
                assignee TEXT,
                due_date DATE,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        logger.info("Tables created successfully")
    
    def store_audio(self, file_path, source=None):
        """
        Store an audio file in the database.
        
        Args:
            file_path (str): Path to the audio file
            source (str, optional): Source of the audio (e.g., 'meeting', 'lecture')
            
        Returns:
            str: UUID of the stored audio file
        """
        filename = os.path.basename(file_path)
        
        # Read the file
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        file_size = os.path.getsize(file_path)
        file_format = filename.split('.')[-1] if '.' in filename else None
        
        # Generate a UUID for the file
        file_id = str(uuid.uuid4())
        
        # Insert the file into the database
        self.cursor.execute("""
            INSERT INTO audio_files (id, filename, file_data, file_size, format, source, recording_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (file_id, filename, psycopg2.Binary(file_data), file_size, file_format, source, datetime.now()))
        
        return file_id
    
    def store_transcription(self, audio_id, text, language='en', confidence=None):
        """
        Store a transcription in the database.
        
        Args:
            audio_id (str): UUID of the audio file
            text (str): Transcription text
            language (str, optional): Language of the transcription
            confidence (float, optional): Confidence score of the transcription
            
        Returns:
            str: UUID of the stored transcription
        """
        transcription_id = str(uuid.uuid4())
        
        self.cursor.execute("""
            INSERT INTO transcriptions (id, audio_id, text, language, confidence)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (transcription_id, audio_id, text, language, confidence))
        
        return transcription_id
    
    def store_summary(self, audio_id, text, version=None):
        """
        Store a summary in the database.
        
        Args:
            audio_id (str): UUID of the audio file
            text (str): Summary text
            version (str, optional): Version of the summarization algorithm
            
        Returns:
            str: UUID of the stored summary
        """
        summary_id = str(uuid.uuid4())
        
        self.cursor.execute("""
            INSERT INTO summaries (id, audio_id, text, version)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (summary_id, audio_id, text, version))
        
        return summary_id
    
    def store_action_item(self, audio_id, text, priority=None, assignee=None, due_date=None, status='pending'):
        """
        Store an action item in the database.
        
        Args:
            audio_id (str): UUID of the audio file
            text (str): Action item text
            priority (str, optional): Priority of the action item
            assignee (str, optional): Person assigned to the action item
            due_date (date, optional): Due date for the action item
            status (str, optional): Current status of the action item
            
        Returns:
            str: UUID of the stored action item
        """
        action_item_id = str(uuid.uuid4())
        
        self.cursor.execute("""
            INSERT INTO action_items (id, audio_id, text, priority, assignee, due_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (action_item_id, audio_id, text, priority, assignee, due_date, status))
        
        return action_item_id
    
    def get_audio(self, audio_id):
        """
        Retrieve an audio file from the database.
        
        Args:
            audio_id (str): UUID of the audio file
            
        Returns:
            tuple: (filename, file_data) or None if not found
        """
        self.cursor.execute("""
            SELECT filename, file_data FROM audio_files
            WHERE id = %s
        """, (audio_id,))
        
        result = self.cursor.fetchone()
        if result:
            return result
        return None
    
    def get_transcription(self, audio_id):
        """
        Retrieve transcription for an audio file.
        
        Args:
            audio_id (str): UUID of the audio file
            
        Returns:
            str: Transcription text or None if not found
        """
        self.cursor.execute("""
            SELECT text FROM transcriptions
            WHERE audio_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (audio_id,))
        
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None
    
    def get_summary(self, audio_id):
        """
        Retrieve summary for an audio file.
        
        Args:
            audio_id (str): UUID of the audio file
            
        Returns:
            str: Summary text or None if not found
        """
        self.cursor.execute("""
            SELECT text FROM summaries
            WHERE audio_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (audio_id,))
        
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None
    
    def get_action_items(self, audio_id):
        """
        Retrieve action items for an audio file.
        
        Args:
            audio_id (str): UUID of the audio file
            
        Returns:
            list: List of action items (dictionaries) or empty list if none found
        """
        self.cursor.execute("""
            SELECT id, text, priority, assignee, due_date, status
            FROM action_items
            WHERE audio_id = %s
            ORDER BY created_at DESC
        """, (audio_id,))
        
        columns = ['id', 'text', 'priority', 'assignee', 'due_date', 'status']
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    def update_action_item_status(self, action_item_id, status):
        """
        Update the status of an action item.
        
        Args:
            action_item_id (str): UUID of the action item
            status (str): New status ('pending', 'in-progress', 'completed', etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.cursor.execute("""
            UPDATE action_items
            SET status = %s
            WHERE id = %s
        """, (status, action_item_id))
        
        return self.cursor.rowcount > 0
    
    def get_audio_with_processed_data(self, audio_id):
        """
        Get audio file with its transcription, summary, and action items.
        
        Args:
            audio_id (str): UUID of the audio file
            
        Returns:
            dict: Dictionary containing audio metadata, transcription, summary, and action items
        """
        # Get audio metadata
        self.cursor.execute("""
            SELECT filename, file_size, duration, format, recording_date, source
            FROM audio_files
            WHERE id = %s
        """, (audio_id,))
        
        audio_columns = ['filename', 'file_size', 'duration', 'format', 'recording_date', 'source']
        audio_result = self.cursor.fetchone()
        
        if not audio_result:
            return None
        
        audio_data = dict(zip(audio_columns, audio_result))
        
        # Get transcription
        transcription = self.get_transcription(audio_id)
        
        # Get summary
        summary = self.get_summary(audio_id)
        
        # Get action items
        action_items = self.get_action_items(audio_id)
        
        return {
            'audio': audio_data,
            'transcription': transcription,
            'summary': summary,
            'action_items': action_items
        }
    
    def close(self):
        """Close the database connection."""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

# Example usage
if __name__ == "__main__":
    db = AudioProcessingDB()
    
    # Add some test code to verify the connection
    try:
        db.cursor.execute("SELECT 1")
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
    finally:
        db.close()
