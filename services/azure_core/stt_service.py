import asyncio
import json
import logging
import io
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()

class UniversalSTTService:
    def __init__(self, api_key: Optional[str] = None):
        self.client = AzureOpenAI(
            api_key=api_key or os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-10-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.logger = logging.getLogger(__name__)
        
    def transcribe_audio(self, audio_bytes: bytes, language: str = "en", industry_context: str = "general") -> Dict[str, Any]:
        """Universal transcription with industry context awareness"""
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"
            
            # Enhanced transcription with context
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language if language != "auto" else None,
                response_format="verbose_json",
                timestamp_granularities=["word"],
                prompt=self._get_industry_prompt(industry_context)
            )
            
            return {
                "text": transcript.text.strip(),
                "language": transcript.language,
                "duration": transcript.duration,
                "words": getattr(transcript, 'words', []),
                "confidence": self._calculate_confidence(transcript.text),
                "speaker_type": self._detect_speaker_type(transcript.text, industry_context),
                "industry_context": industry_context,
                "key_terms": self._extract_industry_terms(transcript.text, industry_context)
            }
            
        except Exception as e:
            self.logger.error(f"STT Error: {e}")
            return {"text": "", "error": str(e), "confidence": 0.0}
    
    def _get_industry_prompt(self, industry: str) -> str:
        """Get industry-specific transcription prompts for better accuracy"""
        prompts = {
            "sales": "B2B sales conversation with terms like ROI, implementation, pricing, features, competition, decision maker, timeline, budget, requirements",
            "real_estate": "Property conversation with terms like BHK, lakhs, crores, location, amenities, possession, home loan, EMI, site visit, booking, registration",
            "general": "Professional business conversation"
        }
        return prompts.get(industry, prompts["general"])
    
    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence score"""
        if not text or len(text.strip()) < 3:
            return 0.0
        word_count = len(text.split())
        return min(0.6 + (word_count * 0.05), 0.95)
    
    def _detect_speaker_type(self, text: str, industry: str) -> str:
        """Detect speaker type based on industry context"""
        text_lower = text.lower().strip()
        
        if industry == "sales":
            # Sales-specific detection
            customer_indicators = ["we need", "our company", "our team", "we are looking", "what about", "how much", "can you"]
            agent_indicators = ["let me show", "our solution", "we provide", "i can help", "our company offers"]
        elif industry == "real_estate":
            # Real estate-specific detection
            customer_indicators = ["i want", "looking for", "my budget", "how much", "when can", "what about"]
            agent_indicators = ["this property", "we have", "i can arrange", "let me show", "the price is"]
        else:
            # General indicators
            customer_indicators = ["i want", "we need", "how much", "when can"]
            agent_indicators = ["we offer", "let me", "i can help", "our service"]
        
        if any(indicator in text_lower for indicator in customer_indicators):
            return "customer"
        elif any(indicator in text_lower for indicator in agent_indicators):
            return "agent"
        
        # Default based on question patterns
        return "customer" if text_lower.endswith('?') or any(q in text_lower for q in ["what", "how", "when", "where", "can"]) else "agent"
    
    def _extract_industry_terms(self, text: str, industry: str) -> list:
        """Extract industry-specific terms for better context"""
        text_lower = text.lower()
        
        industry_terms = {
            "sales": ["roi", "implementation", "pricing", "features", "competition", "budget", "timeline", "decision", "demo", "trial"],
            "real_estate": ["bhk", "lakhs", "crores", "location", "amenities", "possession", "loan", "emi", "site visit", "booking", "sqft"]
        }
        
        terms = industry_terms.get(industry, [])
        return [term for term in terms if term in text_lower]

class StreamingSTTService:
    def __init__(self, on_transcript_callback, industry_context: str = "general"):
        self.stt_service = UniversalSTTService()
        self.on_transcript_callback = on_transcript_callback
        self.industry_context = industry_context
        self.audio_buffer = bytearray()
        self.is_recording = False
        
    def process_audio_chunk(self, audio_chunk: bytes):
        """Process real-time audio chunks"""
        if not self.is_recording:
            self.is_recording = True
            self.audio_buffer = bytearray()
        
        self.audio_buffer.extend(audio_chunk)
        
        # Process when buffer is sufficient (3 seconds at 16kHz)
        if len(self.audio_buffer) > 48000:
            self._process_buffer()
    
    def _process_buffer(self):
        """Process audio buffer and trigger callback"""
        if len(self.audio_buffer) > 8000:  # Minimum 0.5 seconds
            try:
                result = self.stt_service.transcribe_audio(
                    bytes(self.audio_buffer), 
                    industry_context=self.industry_context
                )
                if result.get("text"):
                    asyncio.create_task(self.on_transcript_callback(result))
            except Exception as e:
                logging.error(f"Buffer processing error: {e}")
            
            self.audio_buffer = bytearray()
            self.is_recording = False
    
    def finalize_audio(self):
        """Process remaining audio"""
        if len(self.audio_buffer) > 0:
            self._process_buffer()
