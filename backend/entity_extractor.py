import re
import spacy

class EntityExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def extract_entities(self, transcript):
        doc = self.nlp(transcript)
        people = []
        organizations = []

        for ent in doc.ents:
            if ent.label_ == "PERSON" and not self._is_timestamp(ent.text):
                people.append(ent.text.strip())
            elif ent.label_ == "ORG" and not self._is_timestamp(ent.text):
                organizations.append(ent.text.strip())

        return {
            "people": list(set(people)),
            "organizations": list(set(organizations))
        }

    def _is_timestamp(self, text):
        return bool(re.fullmatch(r'\d{2}:\d{2}(?::\d{2})?', text)) or \
               bool(re.search(r'\d{2}:\d{2}(?::\d{2})?\s*-\s*\d{2}:\d{2}(?::\d{2})?', text))

    def extract_action_items(self, transcript):
        action_items = []

        # Remove timestamps like [00:00:00 - 00:00:05]
        cleaned_transcript = re.sub(r'\[\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}\]\s*', '', transcript)

        # Split into sentences
        doc = self.nlp(cleaned_transcript)
        for sent in doc.sents:
            text = sent.text.strip()

            # Skip common intro/outro or filler lines
            if any(phrase in text.lower() for phrase in [
                "thanks for coming", 
                "if no one has", 
                "let's get started",
                "hello everyone", 
                "thanks again", 
                "we can wrap up", 
                "meeting", 
                "goodbye"
            ]):
                continue

            # Basic heuristic for identifying actionable sentences
            if any(word in text.lower() for word in [
                "let's", "we should", "i will", "i can", "i'll", "you can", "try to", "help out"
            ]):
                action_items.append(text)

        return action_items

    def extract_assignee(self, text):
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text.strip()
        return None

    def process_transcript(self, transcript):
        entities = self.extract_entities(transcript)
        action_texts = self.extract_action_items(transcript)
        action_items = []

        for text in action_texts:
            assignee = self.extract_assignee(text)
            action_items.append({
                "text": text,
                "assignee": assignee if assignee else None,
                "due_date": None
            })

        return {
            "entities": entities,
            "action_items": action_items
        }
