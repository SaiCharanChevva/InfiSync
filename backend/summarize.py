import os
import sys
import argparse
import logging
import torch
from pathlib import Path
from typing import List, Optional, Dict
from transformers import BartTokenizer, BartForConditionalGeneration

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TranscriptSummarizer:
    """
    Summarizes meeting transcripts using BART model.
    """
    
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """
        Initialize the transcript summarizer with a BART model.
        
        Args:
            model_name: HuggingFace model identifier for BART
        """
        logger.info(f"Loading BART model: {model_name}")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        try:
            self.tokenizer = BartTokenizer.from_pretrained(model_name)
            self.model = BartForConditionalGeneration.from_pretrained(model_name).to(self.device)
            logger.info("BART model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading BART model: {e}")
            raise
            
    def _chunk_text(self, text: str, max_length: int = 1024) -> List[str]:
        """
        Split text into chunks that fit within the model's max input length.
        
        Args:
            text: The text to chunk
            max_length: Maximum token length for each chunk
            
        Returns:
            List of text chunks
        """
        # Tokenize the text
        tokens = self.tokenizer.encode(text, return_tensors="pt")[0]
        
        # If text fits in one chunk, return it
        if len(tokens) <= max_length:
            return [text]
            
        # Otherwise, split into chunks
        logger.info(f"Text length ({len(tokens)} tokens) exceeds maximum ({max_length}). Splitting into chunks.")
        
        # Split on paragraph breaks to keep context
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            # Get token length of this paragraph
            paragraph_tokens = self.tokenizer.encode(paragraph)
            paragraph_length = len(paragraph_tokens)
            
            # If adding this paragraph would exceed max length, start a new chunk
            if current_length + paragraph_length > max_length and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_length = 0
                
            # If a single paragraph is too long, split it on sentences
            if paragraph_length > max_length:
                logger.info(f"Long paragraph found ({paragraph_length} tokens). Splitting on sentences.")
                sentences = paragraph.split(". ")
                current_sentence_chunk = []
                current_sentence_length = 0
                
                for sentence in sentences:
                    sentence_tokens = self.tokenizer.encode(sentence)
                    sentence_length = len(sentence_tokens)
                    
                    if current_sentence_length + sentence_length > max_length and current_sentence_chunk:
                        chunks.append(". ".join(current_sentence_chunk) + ".")
                        current_sentence_chunk = []
                        current_sentence_length = 0
                        
                    current_sentence_chunk.append(sentence)
                    current_sentence_length += sentence_length
                    
                if current_sentence_chunk:
                    chunks.append(". ".join(current_sentence_chunk) + ".")
            else:
                current_chunk.append(paragraph)
                current_length += paragraph_length
                
        # Add the final chunk if it's not empty
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
            
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
        
    def summarize(self, text: str, max_length: int = 1024, min_length: int = 150,
                 length_penalty: float = 2.0, num_beams: int = 4,
                 early_stopping: bool = True) -> Dict:
        """
        Summarize the given text using BART.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of the summary
            min_length: Minimum length of the summary
            length_penalty: Length penalty for generation
            num_beams: Number of beams for beam search
            early_stopping: Whether to stop beam search when at least num_beams sentences are finished
            
        Returns:
            Dictionary with summary text and metadata
        """
        # Check if text is empty
        if not text or not text.strip():
            logger.warning("Empty text provided for summarization")
            return {
                "summary": "",
                "chunks_processed": 0,
                "input_length": 0,
                "output_length": 0
            }
            
        # Split text into chunks if necessary
        chunks = self._chunk_text(text, max_length=1024)  # BART max length is typically 1024 tokens
        chunk_summaries = []
        
        logger.info(f"Starting summarization of {len(chunks)} text chunks")
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Summarizing chunk {i+1}/{len(chunks)}")
            
            # Tokenize the chunk
            inputs = self.tokenizer(chunk, return_tensors="pt", truncation=True, max_length=1024).to(self.device)
            
            # Generate summary
            summary_ids = self.model.generate(
                inputs.input_ids,
                max_length=max_length,
                min_length=min_length,
                length_penalty=length_penalty,
                num_beams=num_beams,
                early_stopping=early_stopping
            )
            
            # Decode the summary
            chunk_summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            chunk_summaries.append(chunk_summary)
            
        # Combine chunk summaries
        if len(chunk_summaries) > 1:
            logger.info("Summarizing the combined chunk summaries")
            combined_summary = " ".join(chunk_summaries)
            
            # Do a second summarization pass on the combined summaries if they're too long
            if len(self.tokenizer.encode(combined_summary)) > 1024:
                inputs = self.tokenizer(combined_summary, return_tensors="pt", truncation=True, max_length=1024).to(self.device)
                summary_ids = self.model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    min_length=min_length,
                    length_penalty=length_penalty,
                    num_beams=num_beams,
                    early_stopping=early_stopping
                )
                final_summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            else:
                final_summary = combined_summary
        else:
            final_summary = chunk_summaries[0]
            
        # Calculate stats
        input_length = len(self.tokenizer.encode(text))
        output_length = len(self.tokenizer.encode(final_summary))
        
        logger.info(f"Summarization complete: {input_length} input tokens → {output_length} output tokens")
        
        return {
            "summary": final_summary,
            "chunks_processed": len(chunks),
            "input_length": input_length,
            "output_length": output_length
        }
        
    def format_meeting_summary(self, transcript: str, entities: dict, action_items: list) -> str:
        """
        Generate a comprehensive meeting summary with transcript summary, key entities, and action items.
        
        Args:
            transcript: Meeting transcript
            entities: Entity extraction results
            action_items: List of action items
            
        Returns:
            Formatted meeting summary
        """
        # Get text summary
        summary_result = self.summarize(transcript)
        summary_text = summary_result["summary"]
        
        # Format the comprehensive summary
        formatted_summary = "# Meeting Summary\n\n"
        
        # Add text summary
        formatted_summary += "## Overview\n\n"
        formatted_summary += f"{summary_text}\n\n"
        
        # Add key participants
        if entities.get("people") and len(entities["people"]) > 0:
            formatted_summary += "## Participants\n\n"
            for person in entities["people"]:
                formatted_summary += f"- {person}\n"
            formatted_summary += "\n"
            
        # Add key organizations
        if entities.get("organizations") and len(entities["organizations"]) > 0:
            formatted_summary += "## Organizations Mentioned\n\n"
            for org in entities["organizations"]:
                formatted_summary += f"- {org}\n"
            formatted_summary += "\n"
            
        # Add dates
        if entities.get("dates") and len(entities["dates"]) > 0:
            formatted_summary += "## Key Dates\n\n"
            for date in entities["dates"]:
                formatted_summary += f"- {date}\n"
            formatted_summary += "\n"
            
        # Add action items
        if action_items and len(action_items) > 0:
            formatted_summary += "## Action Items\n\n"
            for item in action_items:
                assignee = f" ({item['assignee']})" if item.get('assignee') else ""
                due_date = f" by {item['due_date']}" if item.get('due_date') else ""
                formatted_summary += f"- {item['text']}{assignee}{due_date}\n"
                
        return formatted_summary

def main():
    parser = argparse.ArgumentParser(description="Summarize meeting transcripts using BART")
    parser.add_argument("transcript_path", help="Path to the transcript file")
    parser.add_argument("--model", default="facebook/bart-large-cnn", help="BART model to use")
    parser.add_argument("--output", help="Output file path (optional)")
    parser.add_argument("--extraction_path", help="Path to entity extraction JSON (optional)")
    parser.add_argument("--max_length", type=int, default=1024, help="Maximum length of the summary")
    parser.add_argument("--min_length", type=int, default=150, help="Minimum length of the summary")
    
    args = parser.parse_args()
    
    # Ensure the transcript file exists
    if not os.path.exists(args.transcript_path):
        logger.error(f"Error: Transcript file not found: {args.transcript_path}")
        return 1
    
    try:
        # Initialize summarizer
        summarizer = TranscriptSummarizer(model_name=args.model)
        
        # Read transcript
        with open(args.transcript_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
            
        # Process extraction results if available
        entities = {}
        action_items = []
        
        if args.extraction_path and os.path.exists(args.extraction_path):
            import json
            with open(args.extraction_path, 'r', encoding='utf-8') as f:
                extraction = json.load(f)
                if 'entities' in extraction:
                    entities = extraction['entities']
                if 'action_items' in extraction:
                    action_items = extraction['action_items']
            
            # Generate formatted summary with entities and action items
            summary = summarizer.format_meeting_summary(transcript, entities, action_items)
        else:
            # Simple summary
            result = summarizer.summarize(
                transcript, 
                max_length=args.max_length,
                min_length=args.min_length
            )
            summary = result["summary"]
            
        # Output the summary
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(summary)
            logger.info(f"Summary saved to {args.output}")
        else:
            print("\n" + "="*80)
            
    except Exception as e:
        logger.error(f"Error during summarization: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())