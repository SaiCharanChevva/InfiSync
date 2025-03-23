import spacy
import re
import json
from typing import Dict, List, Tuple
import os

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
        """
        print(f"Processing text for entities (length: {len(text)} characters)...")
        doc = self.nlp(text)
        print("Text processed by spaCy NLP model")
        
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            if ent.text not in entities[ent.label_]:
                entities[ent.label_].append(ent.text)
        
        print(f"Found {len(doc.ents)} raw entities across {len(entities)} categories")
        
        result = {
            "people": entities.get("PERSON", []),
            "organizations": entities.get("ORG", []),
            "dates": entities.get("DATE", []),
            "locations": [],
            "other_entities": {}
        }
        
        # Combine GPE and LOC entities for locations
        if "GPE" in entities:
            result["locations"].extend(entities["GPE"])
        if "LOC" in entities:
            result["locations"].extend(entities["LOC"])
            
        # Add other entity types
        for ent_type, ents in entities.items():
            if ent_type not in ["PERSON", "ORG", "DATE", "GPE", "LOC"]:
                result["other_entities"][ent_type] = ents
        
        print(f"Found {len(result['people'])} people")
        print(f"Found {len(result['organizations'])} organizations")
        print(f"Found {len(result['dates'])} dates")
        print(f"Found {len(result['locations'])} locations")

        print("Entity extraction completed")
        return result
    
    def extract_action_items(self, text: str) -> List[Dict[str, str]]:
        """
        Extract action items and tasks from the transcript.
        """
        print("Extracting action items...")
        doc = self.nlp(text)
        action_items = []
        
        sentence_count = 0
        for sentence in doc.sents:
            sentence_count += 1
            if self._is_likely_action_item(sentence.text):
                action_items.append({
                    "text": sentence.text.strip(),
                    "assignee": self._extract_assignee(sentence),
                    "due_date": self._extract_due_date(sentence)
                })
        
        print(f"Analyzed {sentence_count} sentences and found {len(action_items)} action items")
        return action_items
    
    def _is_likely_action_item(self, text: str) -> bool:
        """
        Determine if text is likely to be an action item using keyword matching.
        """
        patterns = [
            r'\b(todo|to-do|action item|task)\b',
            r'\b(assign|assigned|will do|will handle|take care of)\b',
            r'\b(follow up|look into|investigate|research)\b',
            r'\b(by tomorrow|by next week|by monday|by tuesday|by wednesday|by thursday|by friday)\b',
            r'\b(needs to|has to|have to|got to|must|should|will)\s+\w+\s+by\b',
            r'\blet\'s\s+\w+\b'
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _extract_assignee(self, sentence) -> str:
        """
        Try to extract who is assigned to the action item.
        """
        for ent in sentence.ents:
            if ent.label_ == "PERSON":
                return ent.text
        
        assignee_indicators = ["I", "you", "he", "she", "we", "they"]
        for token in sentence:
            if token.text in assignee_indicators:
                return token.text
        
        return ""
    
    def _extract_due_date(self, sentence) -> str:
        """
        Try to extract due date from the action item.
        """
        for ent in sentence.ents:
            if ent.label_ == "DATE":
                return ent.text
        
        return ""
    
    def process_transcript(self, transcript: str) -> Dict:
        """
        Process the complete transcript to extract all relevant information.
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
        """
        print(f"Saving extraction results to {output_path}...")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
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
        
        # Save results to JSON
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

print("Script execution complete")