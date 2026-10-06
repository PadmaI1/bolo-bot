import asyncio
import aiohttp
import json
import logging
import time
import io
from typing import Dict, List, Any, Optional
from openai import AsyncAzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class AzureServicesOptimized:
    """Optimized Azure services for unlimited credits scenario"""
    
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-10-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # Store deployment names from environment
        self.model_deployment = os.getenv("AZURE_MODEL_DEPLOYMENT")
        self.stt_deployment = os.getenv("AZURE_STT_DEPLOYMENT")
        
        self.logger = logging.getLogger(__name__)
        
        # Performance optimizations
        self.session = None
        self.connection_pool = None
        self.request_cache = {}  # Simple cache for repeated requests
        
        # Concurrent request management
        self.max_concurrent_requests = 20
        self.request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
    async def initialize(self):
        """Initialize HTTP session with optimal settings"""
        connector = aiohttp.TCPConnector(
            limit=50,  # Maximum connections
            limit_per_host=10,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=5.0)  # 5 second timeout
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
    
    async def generate_text(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 500) -> str:
        """
        Generate text using Azure OpenAI GPT-4
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Creativity (0-1)
            max_tokens: Maximum response length
            
        Returns:
            Generated text string
        """
        async with self.request_semaphore:
            try:
                start_time = time.time()
                
                response = await self.client.chat.completions.create(
                    model=self.model_deployment,  # Use deployment name from environment
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0
                )
                
                text = response.choices[0].message.content.strip()
                processing_time = (time.time() - start_time) * 1000
                
                self.logger.info(f"✅ LLM response generated in {processing_time:.0f}ms")
                return text
                
            except Exception as e:
                self.logger.error(f"❌ LLM generation failed: {e}")
                raise
    
    async def generate_text_lightning(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 100) -> str:
        """
        ⚡ LIGHTNING-FAST text generation for ultra-fast phone responses
        Target: <500ms response time
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Creativity (0-1)
            max_tokens: Maximum response length (optimized for phone calls)
            
        Returns:
            Generated text string
        """
        async with self.request_semaphore:
            try:
                start_time = time.time()
                
                response = await self.client.chat.completions.create(
                    model=self.model_deployment,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,  # Shorter for faster response
                    top_p=0.9,              # Slightly lower for speed
                    frequency_penalty=0,
                    presence_penalty=0
                )
                
                text = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
                processing_time = (time.time() - start_time) * 1000
                
                # Log performance for optimization
                if processing_time < 500:
                    self.logger.info(f"⚡ LIGHTNING LLM: {processing_time:.0f}ms ✅")
                else:
                    self.logger.warning(f"⚠️ SLOW LLM: {processing_time:.0f}ms")
                
                # CRITICAL: Check for empty or whitespace-only responses
                if not text or text.strip() == "":
                    self.logger.error("❌ LLM returned empty text! Prompts may need improvement.")
                    # Return empty so calling code can handle with context-aware fallback
                    return ""
                
                return text
                
            except Exception as e:
                self.logger.error(f"❌ Lightning LLM failed: {e}")
                # Return empty so calling code handles fallback with context
                return ""
    
    async def transcribe_audio_optimized(self, audio_data: bytes, language: str = "en") -> Dict[str, Any]:
        """Ultra-fast audio transcription with Azure STT"""
        async with self.request_semaphore:
            try:
                start_time = time.time()
                
                # Convert audio bytes to file-like object
                audio_file = io.BytesIO(audio_data)
                audio_file.name = "audio.wav"
                
                # Use Azure OpenAI Whisper with optimized parameters
                response = await self.client.audio.transcriptions.create(
                    model=self.stt_deployment,  # Use deployment name from environment
                    file=audio_file,
                    language=language if language != "auto" else None,
                    response_format="json",  # Faster than verbose_json
                    temperature=0.0,  # Deterministic for faster processing
                    prompt="Professional business conversation"  # Context for better accuracy
                )
                
                processing_time = (time.time() - start_time) * 1000
                
                return {
                    "text": response.text.strip(),
                    "confidence": 0.95,  # High confidence with good audio
                    "language": language,
                    "processing_time_ms": processing_time,
                    "word_count": len(response.text.split()),
                    "speaker_detected": self._detect_speaker_type(response.text)
                }
                
            except Exception as e:
                self.logger.error(f"STT Error: {e}")
                return {
                    "text": "",
                    "confidence": 0.0,
                    "error": str(e),
                    "processing_time_ms": (time.time() - start_time) * 1000
                }
    
    async def analyze_conversation_advanced(self, 
                                          transcript: str, 
                                          industry: str, 
                                          conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced conversation analysis with GPT-4"""
        async with self.request_semaphore:
            try:
                start_time = time.time()
                
                # Industry-specific system prompts
                system_prompts = {
                    "sales": self._get_sales_analysis_prompt(),
                    "real_estate": self._get_realestate_analysis_prompt()
                }
                
                system_prompt = system_prompts.get(industry, system_prompts["sales"])
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": self._build_analysis_request(transcript, conversation_context)}
                ]
                
                # Use GPT-4 with optimized parameters for speed and quality
                response = await self.client.chat.completions.create(
                    model=self.model_deployment,  # Use deployment name from environment
                    messages=messages,
                    max_tokens=800,
                    temperature=0.3,
                    top_p=0.9,
                    frequency_penalty=0.1,
                    presence_penalty=0.1,
                    response_format={"type": "json_object"}  # Structured response
                )
                
                processing_time = (time.time() - start_time) * 1000
                
                # Parse and validate response
                analysis_result = json.loads(response.choices[0].message.content)
                analysis_result["processing_time_ms"] = processing_time
                analysis_result["model_used"] = "gpt-4o"
                analysis_result["industry"] = industry
                
                return analysis_result
                
            except Exception as e:
                self.logger.error(f"Analysis Error: {e}")
                return {
                    "error": str(e),
                    "fallback_response": "Continue the conversation naturally",
                    "processing_time_ms": (time.time() - start_time) * 1000
                }
    
    def _get_sales_analysis_prompt(self) -> str:
        return """You are an expert B2B sales coach providing real-time analysis of sales conversations.

Your expertise includes:
- Discovery questioning techniques and BANT qualification
- Value-based selling and ROI articulation  
- Objection handling with proven response frameworks
- Competitor positioning and battle card activation
- Deal progression and next step recommendations
- Indian B2B market dynamics and cultural nuances

Analyze the conversation and respond with JSON containing:
{
  "conversation_stage": "discovery/presentation/objection_handling/closing",
  "sentiment": {
    "customer_mood": "positive/neutral/negative/frustrated",
    "engagement_level": "high/medium/low",
    "buying_signals": ["signal1", "signal2"],
    "urgency_indicators": ["indicator1", "indicator2"]
  },
  "coaching_insights": {
    "immediate_action": "specific action for sales rep right now",
    "discovery_questions": ["question1", "question2"],
    "value_propositions": ["value1", "value2"],
    "risk_alerts": ["risk1", "risk2"]
  },
  "objection_handling": {
    "objection_type": "price/timing/features/competition/none",
    "objection_severity": "high/medium/low",
    "recommended_response": "specific response script",
    "follow_up_strategy": "next steps after objection"
  },
  "competitor_analysis": {
    "competitor_mentioned": "competitor name or null",
    "competitive_threat_level": "high/medium/low",
    "differentiation_points": ["point1", "point2"],
    "battle_card_needed": true/false
  },
  "deal_progression": {
    "progression_score": 1-10,
    "next_best_action": "specific next step",
    "timeline_urgency": "immediate/this_week/this_month/long_term",
    "close_probability": "percentage estimate"
  },
  "crm_insights": {
    "key_discussion_points": ["point1", "point2"],
    "action_items": ["action1", "action2"],
    "follow_up_date": "suggested date",
    "deal_stage_update": "stage recommendation"
  }
}"""

    def _get_realestate_analysis_prompt(self) -> str:
        return """You are a professional real estate consultant specializing in Indian property markets and lead qualification.

Your expertise includes:
- Lead qualification and budget assessment (₹20L-₹10Cr range)
- Property type matching and location analysis
- Investment vs self-use buyer identification
- Home loan guidance and EMI calculations
- Cultural aspects of Indian property buying decisions
- Market trends and pricing strategies

Analyze the conversation and respond with JSON containing:
{
  "lead_qualification": {
    "quality_score": 1-10,
    "qualification_stage": "initial/budget_discussion/requirement_gathering/ready_to_visit",
    "conversion_probability": "high/medium/low",
    "qualification_completeness": "percentage"
  },
  "customer_profile": {
    "buyer_type": "first_time/upgrader/investor/end_user",
    "budget_range": "detected range in lakhs/crores or not_disclosed",
    "budget_flexibility": "high/medium/low",
    "financing_status": "loan_required/cash_buyer/exploring_options",
    "decision_timeline": "immediate/1-3months/3-6months/exploring",
    "family_involvement": "self/spouse/parents/joint_family_decision"
  },
  "property_requirements": {
    "property_type": "apartment/villa/plot/commercial/flexible",
    "size_preference": "1bhk/2bhk/3bhk/4bhk+/flexible",
    "location_preferences": ["location1", "location2"],
    "key_amenities_wanted": ["amenity1", "amenity2"],
    "possession_preference": "ready_to_move/under_construction/flexible"
  },
  "conversation_insights": {
    "pain_points": ["current housing challenge1", "challenge2"],
    "motivation_factors": ["why buying now1", "factor2"],
    "concerns_objections": ["concern1", "concern2"],
    "positive_indicators": ["interest1", "interest2"]
  },
  "next_actions": {
    "immediate_priority": "send_properties/schedule_visit/detailed_call/follow_up",
    "recommended_timeline": "today/tomorrow/this_week/next_week",
    "property_types_to_show": ["type1", "type2"],
    "additional_qualification_needed": ["info1", "info2"]
  },
  "agent_coaching": {
    "conversation_effectiveness": "excellent/good/average/needs_improvement", 
    "missed_opportunities": ["opportunity1", "opportunity2"],
    "recommended_questions": ["question1", "question2"],
    "closing_approach": "technique to use for next steps"
  }
}"""
    
    def _build_analysis_request(self, transcript: str, context: Dict[str, Any]) -> str:
        return f"""Analyze this conversation:

Recent Transcript: {transcript}

Context Information:
- Session Duration: {context.get('duration_minutes', 0)} minutes
- Previous Messages: {context.get('message_count', 0)}
- Industry: {context.get('industry', 'unknown')}
- Customer Profile: {json.dumps(context.get('customer_info', {}), indent=2)}

Provide detailed analysis in the specified JSON format."""
    
    def _detect_speaker_type(self, text: str) -> str:
        """Simple speaker detection based on patterns"""
        text_lower = text.lower()
        
        # Customer indicators (questions, inquiries)
        customer_patterns = ["what", "how", "when", "where", "can you", "do you have", "i want", "i need", "how much"]
        if any(pattern in text_lower for pattern in customer_patterns):
            return "customer"
        
        # Agent indicators (responses, offers)
        agent_patterns = ["let me", "i can", "we have", "our", "would you like", "i'll help"]
        if any(pattern in text_lower for pattern in agent_patterns):
            return "agent"
        
        return "unknown"
    
    async def close(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
