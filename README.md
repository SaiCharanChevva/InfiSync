An intelligent meeting summarization tool that converts recorded sessions into concise, structured summaries with key information extraction.
Overview
This project automates the process of meeting documentation by:
1. Transcribing recorded audio/video using OpenAI's Whisper model
2. Summarizing the content using the BART model
3. Extracting key information (people, organizations, dates, action items) using Named Entity Recognition (NER)
Features
* Speech-to-Text Transcription: Accurate conversion of spoken content to text using OpenAI's Whisper model
* Intelligent Summarization: Generation of concise meeting summaries using BART
* Key Information Extraction: Identification of important entities, action items, and decisions using NER
* User-Friendly Interface: Easy-to-use interface for uploading recordings and viewing results
Technology Stack
* Speech Recognition: OpenAI Whisper
* Summarization: BART (Bidirectional and Auto-Regressive Transformers)
* Entity Recognition: Spacy/Hugging Face NER models
* Backend: Python, Flask/FastAPI
