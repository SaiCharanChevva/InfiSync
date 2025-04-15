import spacy
import re
import json
import os
from typing import Dict, List, Tuple

# Custom pipeline component for spaCy to detect action items
@spacy.language.Language.component("action_item_detector")
def action_item_detector(doc):
    """Custom spaCy component to mark sentences as action items"""
    return doc

class EntityExtractor:
    """
    Extracts entities and action items from meeting transcripts using NER.
    """
    
    def __init__(self, model_name: str = "en_core_web_lg"):
        """
        Initialize the entity extractor with a spaCy model.
        
        Args:
            model_name: Name of the spaCy model to use
        """
        print(f"Loading spaCy model: {model_name}")
        try:
            self.nlp = spacy.load(model_name)
            print("spaCy model loaded successfully")
        except OSError:
            print(f"Model {model_name} not found. Downloading...")
            spacy.cli.download(model_name)
            self.nlp = spacy.load(model_name)
            print("Model downloaded and loaded successfully")
        
        # Add custom pipeline components for action item detection
        if "action_item_detector" not in self.nlp.pipe_names:
            self.nlp.add_pipe("action_item_detector", last=True)
            print("Added action item detector to pipeline")
        
        print("Entity extraction model loaded successfully")
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text.
        
        Args:
            text: The transcript text
            
        Returns:
            Dictionary of entity types and their values
        """
        print(f"Processing text for entities (length: {len(text)} characters)...")
        doc = self.nlp(text)
        print("Text processed by spaCy NLP model")
        
        # Group entities by type
        print("Extracting entities...")
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            
            # Add entity if not already in the list
            if ent.text not in entities[ent.label_]:
                entities[ent.label_].append(ent.text)
        
        print(f"Found {len(doc.ents)} raw entities across {len(entities)} categories")
        
        # Create a more user-friendly structure with common entity types
        result = {
            "people": [],
            "organizations": [],
            "dates": [],
            "locations": [],
            "other_entities": {}
        }
        
        # Map spaCy entity types to our structure
        if "PERSON" in entities:
            result["people"] = entities["PERSON"]
            print(f"Found {len(entities['PERSON'])} people")
        
        if "ORG" in entities:
            result["organizations"] = entities["ORG"]
            print(f"Found {len(entities['ORG'])} organizations")
        
        if "DATE" in entities:
            result["dates"] = entities["DATE"]
            print(f"Found {len(entities['DATE'])} dates")
        
        if "GPE" in entities or "LOC" in entities:
            locs = []
            if "GPE" in entities:
                locs.extend(entities["GPE"])
            if "LOC" in entities:
                locs.extend(entities["LOC"])
            result["locations"] = locs
            print(f"Found {len(locs)} locations")
        
        # Add other entity types
        for ent_type, ents in entities.items():
            if ent_type not in ["PERSON", "ORG", "DATE", "GPE", "LOC"]:
                result["other_entities"][ent_type] = ents
        
        print("Entity extraction completed")
        return result
    
    def extract_action_items(self, text: str) -> List[Dict[str, str]]:
        """
        Extract action items and tasks from the transcript.
        
        Args:
            text: The transcript text
            
        Returns:
            List of action items with details
        """
        print("Extracting action items...")
        doc = self.nlp(text)
        action_items = []
        
        # Get action items from the custom pipeline component
        sentence_count = 0
        for sentence in doc.sents:
            sentence_count += 1
            # Look for common action item patterns
            if self._is_likely_action_item(sentence.text):
                # Extract assignee if available
                assignee = self._extract_assignee(sentence)
                
                # Extract due date if available
                due_date = self._extract_due_date(sentence)
                
                # Extract the task content
                task_content = self._extract_task_content(sentence.text)
                
                action_items.append({
                    "text": sentence.text.strip(),
                    "task": task_content,
                    "assignee": assignee,
                    "due_date": due_date
                })
        
        print(f"Analyzed {sentence_count} sentences and found {len(action_items)} action items")
        return action_items
    
    def _is_likely_action_item(self, text: str) -> bool:
        """
        Determine if text is likely to be an action item using keyword matching.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if likely an action item, False otherwise
        """
        # More comprehensive action item indicators
        action_verbs = r'\b(create|update|prepare|review|send|share|complete|implement|develop|research|investigate|schedule|call|email|finalize|deliver|submit|check|analyze|test|write|draft|confirm|follow up|follow-up|upload|set up|coordinate|organize|arrange)\b'
        
        assignment_patterns = [
            r'\b(will|shall|must|need to|going to|have to|assigned to|responsible for)\b',
            r'\b(todo|to-do|action item|task|action|deliverable|next step)\b',
            r'\b(let\'s|we should|team will|team should|let us)\b',
            r'\b(by (monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|next week|end of|month|quarter))\b',
            r'\b(due (today|tomorrow|this week|next week|by|on|before))\b',
            r'\b(please|kindly|can you|could you)\s+\w+\b',
            r'I\'ll\s+\w+\b',
            r'You\'ll\s+\w+\b',
            r'We\'ll\s+\w+\b',
            r'They\'ll\s+\w+\b'
        ]
        
        syntax_patterns = [
            # Imperative sentences (commands)
            r'^[A-Z][^.!?]*\s+' + action_verbs + r'[^.!?]*$',
            
            # First person commitment
            r'\bI\s+(will|\'ll|am going to|can|could|shall|should|would|might)\s+' + action_verbs,
            
            # Assignment to others
            r'\b(You|We|They|He|She|Name)\s+(will|\'ll|are going to|can|should|would|need to)\s+' + action_verbs
        ]
        
        text_lower = text.lower()
        
        # Check for action verbs in text
        if re.search(action_verbs, text_lower):
            # If it has an action verb, check for assignment/timing patterns
            for pattern in assignment_patterns:
                if re.search(pattern, text_lower):
                    return True
                    
        # Check for syntactic patterns even if no assignment words found
        for pattern in syntax_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
                
        # Additional check for colon-prefixed task lists
        if re.search(r'(task|action item|todo|to do|deliverable)\s*:\s*', text_lower):
            return True
            
        return False
    
    def _extract_task_content(self, text: str) -> str:
        """
        Extract the core task description from the action item text.
        
        Args:
            text: The action item text
            
        Returns:
            The core task content
        """
        # Remove common prefixes like "Action item:" or "TODO:"
        task_content = re.sub(r'^(action item|task|todo|to-do|deliverable)\s*:\s*', '', text, flags=re.IGNORECASE)
        
        # Remove assignment phrases
        assignment_phrases = [
            r'I will\s+',
            r'I\'ll\s+',
            r'You will\s+',
            r'You\'ll\s+',
            r'We will\s+',
            r'We\'ll\s+',
            r'Please\s+',
            r'Can you\s+',
            r'Could you\s+',
            r'needs to\s+',
            r'assigned to\s+[\w\s]+:',
            r'is responsible for\s+',
        ]
        
        for phrase in assignment_phrases:
            task_content = re.sub(phrase, '', task_content, flags=re.IGNORECASE)
            
        # Clean up the result
        task_content = task_content.strip()
        
        return task_content
    
    def _extract_assignee(self, sentence) -> str:
        """
        Try to extract who is assigned to the action item.
        
        Args:
            sentence: spaCy sentence
            
        Returns:
            Extracted assignee or empty string
        """
        # Look for person entities near action words
        for ent in sentence.ents:
            if ent.label_ == "PERSON":
                return ent.text
        
        # Look for pronouns that might indicate assignees
        assignee_indicators = ["I", "you", "he", "she", "we", "they"]
        for token in sentence:
            if token.text in assignee_indicators:
                return token.text
        
        return ""
    
    def _extract_due_date(self, sentence) -> str:
        """
        Try to extract due date from the action item.
        
        Args:
            sentence: spaCy sentence
            
        Returns:
            Extracted due date or empty string
        """
        for ent in sentence.ents:
            if ent.label_ == "DATE":
                return ent.text
        
        return ""
    
    def process_transcript(self, transcript: str) -> Dict:
        """
        Process the complete transcript to extract all relevant information.
        
        Args:
            transcript: The full meeting transcript
            
        Returns:
            Dictionary with extracted entities and action items
        """
        print(f"Processing transcript of length: {len(transcript)} characters")
        
        print("Extracting named entities...")
        entities = self.extract_entities(transcript)
        
        print("Extracting action items...")
        action_items = self.extract_action_items(transcript)
        
        print("Transcript processing completed")
        return {
            "entities": entities,
            "action_items": action_items
        }
    
    def save_results(self, results: Dict, output_path: str) -> None:
        """
        Save extraction results to a JSON file.
        
        Args:
            results: The extraction results
            output_path: Path to save the results
        """
        print(f"Saving extraction results to {output_path}...")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            # Verify file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"Results saved to {output_path} ({file_size} bytes)")
            else:
                print(f"Warning: Output file {output_path} was not created")
                
        except Exception as e:
            print(f"Error saving results: {e}")
            import traceback
            traceback.print_exc()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract entities and action items from meeting transcript")
    parser.add_argument("transcript_path", help="Path to the transcript file")
    parser.add_argument("--model", default="en_core_web_lg", help="spaCy model to use")
    parser.add_argument("--output", default="extraction_results.json", help="Output file path")
    
    args = parser.parse_args()
    
    try:
        if not os.path.exists(args.transcript_path):
            print(f"Error: Transcript file not found: {args.transcript_path}")
            return
            
        print(f"Initializing entity extractor with model: {args.model}")
        extractor = EntityExtractor(model_name=args.model)
        
        with open(args.transcript_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
        
        print(f"Successfully read transcript: {len(transcript)} characters")
        
        results = extractor.process_transcript(transcript)
        
        # Save results to JSONpyp[pp]
        extractor.save_results(results, args.output)
        
        # Print summary
        print("\nExtraction Summary:")
        print(f"People mentioned: {len(results['entities']['people'])}")
        print(f"Organizations mentioned: {len(results['entities']['organizations'])}")
        print(f"Dates mentioned: {len(results['entities']['dates'])}")
        print(f"Action items found: {len(results['action_items'])}")
    
    except Exception as e:
        print(f"Error during entity extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()