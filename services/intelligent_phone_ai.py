"""
Intelligent Phone AI Agent - Real-time, context-aware conversations
Powered by Azure OpenAI + Murf AI with minimal latency
Supports: B2B Sales (Murf API) & Real Estate (JK Ventures Hyderabad)
Languages: English, Hindi, Telugu (seamless switching)
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

class IntelligentPhoneAI:
    """
    Ultra-smart AI agent for phone conversations
    - Dynamic response generation (not hardcoded)
    - Multi-language support (English, Hindi, Telugu)
    - Context awareness and memory
    - Natural conversation flow
    """
    
    def __init__(self, azure_service, murf_service):
        self.azure_service = azure_service
        self.murf_service = murf_service
        self.logger = logging.getLogger(__name__)
        
        # Active conversations with full context
        self.conversations: Dict[str, Dict[str, Any]] = {}
        
        # Voice selection based on language and gender
        self.voice_profiles = {
            "en-IN": {  # English India
                "male": ["en-IN-eashwar", "en-IN-rohan"],
                "female": ["en-IN-priya", "en-IN-alia"]
            },
            "hi-IN": {  # Hindi India
                "male": ["hi-IN-kabir"],
                "female": ["hi-IN-ayushi"]
            },
            "te-IN": {  # Telugu India
                "male": ["te-IN-mohan"],
                "female": ["te-IN-shruti"]
            }
        }
        
        # Agent personas
        self.personas = {
            "b2b_sales": {
                "name": "Priya Sharma",
                "company": "Murf AI",
                "role": "Enterprise Solutions Specialist",
                "voice_id": "en-IN-priya",
                "voice_style": "Conversational",
                "personality": "Professional, friendly, knowledgeable about Murf API",
                "expertise": "AI voice synthesis, API integration, enterprise solutions",
                "goal": "Understand customer's voice needs and demonstrate Murf API value"
            },
            "real_estate": {
                "name": "Rohan Reddy",
                "company": "JK Ventures",
                "role": "Senior Property Consultant",
                "voice_id": "en-IN-rohan",
                "voice_style": "Conversational",
                "personality": "Warm, expert on Hyderabad real estate, trustworthy",
                "expertise": "Hyderabad properties, investment guidance, market insights",
                "goal": "Qualify leads and match them with perfect properties in Hyderabad"
            }
        }
        
        self.logger.info("🤖 Intelligent Phone AI initialized - Ready for smart conversations")
    
    async def start_conversation(
        self,
        call_sid: str,
        call_type: str,
        lead_info: Dict[str, Any],
        preferred_language: str = "en-IN"
    ) -> Dict[str, Any]:
        """
        Start a new intelligent conversation
        
        Args:
            call_sid: Twilio call SID
            call_type: 'b2b_sales' or 'real_estate'
            lead_info: Customer information (name, company, etc.)
            preferred_language: 'en-IN', 'hi-IN', or 'te-IN'
        """
        persona = self.personas[call_type]
        
        # Initialize conversation context
        self.conversations[call_sid] = {
            "call_sid": call_sid,
            "call_type": call_type,
            "persona": persona,
            "lead_info": lead_info,
            "language": preferred_language,
            "conversation_history": [],
            "context": {
                "stage": "opening",
                "topics_discussed": [],
                "customer_sentiment": "neutral",
                "key_information": {},
                "next_objectives": []
            },
            "started_at": datetime.now().isoformat()
        }
        
        # Generate opening message
        opening = await self._generate_opening_message(call_sid)
        
        return opening
    
    async def _generate_opening_message(self, call_sid: str) -> Dict[str, Any]:
        """Generate personalized opening message based on call type and lead info"""
        conv = self.conversations[call_sid]
        persona = conv["persona"]
        lead_info = conv["lead_info"]
        lead_name = lead_info.get("name", "there")
        
        if conv["call_type"] == "b2b_sales":
            # Murf API sales call with VALUE PROPOSITION
            prompt = f"""You are {persona['name']}, an {persona['role']} at {persona['company']}.

PRODUCT: Murf AI Text-to-Speech API
- Converts text to ultra-realistic voice in 20+ languages
- 120+ AI voices (like mine)
- Simple REST API integration
- Use cases: E-learning, IVR, marketing, audiobooks, podcasts
- Key benefit: Save 80% time & cost vs hiring voice actors

You're calling {lead_name} to introduce this solution.

Generate a compelling opening that:
1. Greets and confirms {lead_name}
2. Introduces yourself from Murf AI
3. Mentions ONE specific benefit (save time/cost on voice content)
4. Asks for 2-3 minutes
5. Keep under 30 words total

Example: "Hi {lead_name}, this is {persona['name']} from Murf AI. I'm calling about our Text-to-Speech API that helps businesses cut voice production costs by 80%. Do you have 2 minutes to chat?"

Generate natural opening:"""
        
        else:  # real_estate
            # JK Ventures real estate call with PROPERTY SPECIFICS
            prompt = f"""You are {persona['name']}, a {persona['role']} at {persona['company']}.

PROPERTIES: Hyderabad Premium Real Estate
- Locations: Gachibowli, Hitec City, Jubilee Hills, Banjara Hills
- 2BHK: ₹60L-1.2Cr | 3BHK: ₹1-2.5Cr | Villas: ₹2.5Cr+
- RERA approved, ready-to-move and under-construction
- Investment returns: 8-12% annually

You're calling {lead_name} about their property interest in Hyderabad.

Generate a warm opening that:
1. Greets and confirms {lead_name}
2. Introduces yourself from JK Ventures
3. References Hyderabad properties
4. Creates interest with one detail (location/new listing)
5. Keep under 30 words

Example: "Hi {lead_name}, this is {persona['name']} from JK Ventures. I'm calling about premium properties in Hyderabad - we have excellent new 3BHK options in Gachibowli. Do you have a moment?"

Generate natural opening:"""
        
        # Get AI response - Convert to message array format
        messages = [
            {"role": "system", "content": f"You are {persona['name']}, {persona['role']} at {persona['company']}. Generate natural, conversational phone call openings."},
            {"role": "user", "content": prompt}
        ]
        opening_text = await self.azure_service.generate_text(messages)
        opening_text = opening_text.strip()
        
        # Detect language and select voice
        language = self._detect_language(opening_text)
        voice_id = self._select_voice(language, persona)
        
        # Store in conversation history
        self._add_message(call_sid, "agent", opening_text)
        
        return {
            "text": opening_text,
            "voice_id": voice_id,
            "language": language,
            "emotion": "friendly",
            "stage": "opening"
        }
    
    async def process_customer_response(
        self,
        call_sid: str,
        customer_speech: str
    ) -> Dict[str, Any]:
        """
        Process customer's speech and generate intelligent response
        This is where the AI "thinks" and responds naturally
        
        Args:
            call_sid: Call identifier
            customer_speech: Transcribed customer speech from Twilio
        
        Returns:
            AI-generated response with voice parameters
        """
        if call_sid not in self.conversations:
            return {"error": "Conversation not found"}
        
        conv = self.conversations[call_sid]
        persona = conv["persona"]
        
        # Store customer message
        self._add_message(call_sid, "customer", customer_speech)
        
        # Detect customer's language
        customer_language = self._detect_language(customer_speech)
        conv["language"] = customer_language  # Switch to customer's language
        
        # Analyze customer intent and sentiment
        analysis = await self._analyze_customer_intent(call_sid, customer_speech)
        
        # Generate intelligent response
        ai_response = await self._generate_intelligent_response(
            call_sid,
            customer_speech,
            analysis
        )
        
        # Store agent response
        self._add_message(call_sid, "agent", ai_response["text"])
        
        # Update conversation context
        self._update_context(call_sid, analysis)
        
        return ai_response
    
    async def _analyze_customer_intent(
        self,
        call_sid: str,
        customer_speech: str
    ) -> Dict[str, Any]:
        """Analyze what customer wants/means"""
        conv = self.conversations[call_sid]
        
        prompt = f"""Analyze this customer response in a sales call:

Customer said: "{customer_speech}"

Determine:
1. Intent: interested/not_interested/has_question/wants_details/objection/positive_signal
2. Sentiment: positive/neutral/negative
3. Key information: any specific details they mentioned
4. Buying signals: yes/no
5. Language: en/hi/te

Return as JSON:
{{
    "intent": "...",
    "sentiment": "...",
    "key_info": {{}},
    "buying_signal": false,
    "language": "en"
}}"""
        
        # Convert to message array format
        messages = [
            {"role": "system", "content": "You are a conversation analyzer. Return only valid JSON format with no additional text."},
            {"role": "user", "content": prompt}
        ]
        analysis_text = await self.azure_service.generate_text(messages)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = {
                    "intent": "interested",
                    "sentiment": "neutral",
                    "key_info": {},
                    "buying_signal": False,
                    "language": "en"
                }
        except:
            analysis = {
                "intent": "interested",
                "sentiment": "neutral",
                "key_info": {},
                "buying_signal": False,
                "language": "en"
            }
        
        return analysis
    
    async def _generate_intelligent_response(
        self,
        call_sid: str,
        customer_speech: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate smart, context-aware response"""
        conv = self.conversations[call_sid]
        persona = conv["persona"]
        call_type = conv["call_type"]
        context = conv["context"]
        history = self._get_conversation_summary(call_sid)
        
        if call_type == "b2b_sales":
            system_context = f"""You are {persona['name']}, {persona['role']} at {persona['company']}.

Your expertise: {persona['expertise']}
Your goal: {persona['goal']}

About Murf AI:
- Premium text-to-speech API with 161 AI voices in 20+ languages
- Gen2 model for ultra-realistic voices
- Use cases: IVR systems, e-learning, audiobooks, content creation, voice assistants
- Easy integration with REST API and WebSockets
- Pricing based on characters (cost-effective)
- Enterprise features: Custom voices, batch processing, analytics

Conversation so far:
{history}

Customer just said: "{customer_speech}"
Customer intent: {analysis['intent']}
Customer sentiment: {analysis['sentiment']}

Generate your response as {persona['name']}:
- Be conversational and natural
- Address their specific question/concern
- Highlight relevant Murf AI benefits
- Ask intelligent follow-up questions
- Keep response under 40 words
- Match their language (English/Hindi/Telugu)
- Sound human, not scripted

Response:"""
        
        else:  # real_estate
            system_context = f"""You are {persona['name']}, {persona['role']} at {persona['company']}.

Your expertise: {persona['expertise']}
Your goal: {persona['goal']}

About JK Ventures:
- Specialized in Hyderabad residential and commercial properties
- Hot areas: Gachibowli, HITEC City, Madhapur, Financial District, Miyapur
- Price range: 50L - 5Cr (apartments, villas, plots)
- Amenities: Clubhouse, gym, swimming pool, 24/7 security
- Investment potential: 8-12% appreciation annually
- Home loan assistance available

Conversation so far:
{history}

Customer just said: "{customer_speech}"
Customer intent: {analysis['intent']}
Customer sentiment: {analysis['sentiment']}

Generate your response as {persona['name']}:
- Be warm and consultative
- Address their property needs
- Share relevant market insights
- Ask qualifying questions (budget, location preference, timeline)
- Keep response under 40 words
- Match their language (English/Hindi/Telugu)
- Sound like a trusted advisor

Response:"""
        
        # Generate AI response - Convert to message array format
        messages = [
            {"role": "system", "content": f"You are {persona['name']}, {persona['role']} at {persona['company']}. Generate natural, conversational phone responses."},
            {"role": "user", "content": system_context}
        ]
        response_text = await self.azure_service.generate_text(messages)
        response_text = response_text.strip()
        
        # Detect language and select voice
        language = self._detect_language(response_text)
        voice_id = self._select_voice(language, persona)
        
        # Determine if call should continue or end
        should_continue = self._should_continue_call(analysis, response_text)
        
        return {
            "text": response_text,
            "voice_id": voice_id,
            "language": language,
            "emotion": self._determine_emotion(analysis),
            "should_continue": should_continue,
            "stage": context["stage"]
        }
    
    def _detect_language(self, text: str) -> str:
        """Detect language from text (simple heuristic)"""
        # Check for Devanagari script (Hindi)
        if any('\u0900' <= char <= '\u097F' for char in text):
            return "hi-IN"
        
        # Check for Telugu script
        if any('\u0C00' <= char <= '\u0C7F' for char in text):
            return "te-IN"
        
        # Default to English
        return "en-IN"
    
    def _select_voice(self, language: str, persona: Dict[str, Any]) -> str:
        """Select appropriate Murf voice based on language and persona"""
        # Use persona's default voice if same language
        if language == "en-IN":
            return persona["voice_id"]
        
        # For other languages, select gender-appropriate voice
        if language in self.voice_profiles:
            gender = "female" if "priya" in persona["voice_id"] or "alia" in persona["voice_id"] else "male"
            voices = self.voice_profiles[language][gender]
            return voices[0] if voices else persona["voice_id"]
        
        return persona["voice_id"]
    
    def _determine_emotion(self, analysis: Dict[str, Any]) -> str:
        """Determine emotion/tone for voice synthesis"""
        sentiment = analysis.get("sentiment", "neutral")
        
        if sentiment == "positive":
            return "friendly"
        elif sentiment == "negative":
            return "empathetic"
        else:
            return "conversational"
    
    def _should_continue_call(self, analysis: Dict[str, Any], response: str) -> bool:
        """Determine if call should continue or end"""
        intent = analysis.get("intent", "")
        
        # End call if customer wants to end
        end_keywords = ["not interested", "don't call", "remove", "bye", "later", "busy"]
        if any(keyword in response.lower() for keyword in end_keywords):
            return False
        
        if intent == "not_interested":
            return False
        
        # Continue for all other intents
        return True
    
    def _add_message(self, call_sid: str, role: str, text: str):
        """Add message to conversation history"""
        if call_sid in self.conversations:
            self.conversations[call_sid]["conversation_history"].append({
                "role": role,
                "text": text,
                "timestamp": datetime.now().isoformat()
            })
    
    def _get_conversation_summary(self, call_sid: str, last_n: int = 4) -> str:
        """Get recent conversation summary"""
        if call_sid not in self.conversations:
            return ""
        
        history = self.conversations[call_sid]["conversation_history"][-last_n:]
        summary = []
        
        for msg in history:
            role_name = "Agent" if msg["role"] == "agent" else "Customer"
            summary.append(f"{role_name}: {msg['text']}")
        
        return "\n".join(summary)
    
    def _update_context(self, call_sid: str, analysis: Dict[str, Any]):
        """Update conversation context based on analysis"""
        if call_sid not in self.conversations:
            return
        
        context = self.conversations[call_sid]["context"]
        
        # Update sentiment
        context["customer_sentiment"] = analysis.get("sentiment", "neutral")
        
        # Store key information
        key_info = analysis.get("key_info", {})
        context["key_information"].update(key_info)
        
        # Update stage based on conversation progress
        history_length = len(self.conversations[call_sid]["conversation_history"])
        if history_length < 4:
            context["stage"] = "opening"
        elif history_length < 8:
            context["stage"] = "discovery"
        elif history_length < 12:
            context["stage"] = "qualification"
        else:
            context["stage"] = "closing"
    
    async def generate_closing_message(self, call_sid: str, reason: str = "completed") -> str:
        """Generate natural closing message"""
        if call_sid not in self.conversations:
            return "Thank you for your time. Goodbye!"
        
        conv = self.conversations[call_sid]
        persona = conv["persona"]
        
        if reason == "not_interested":
            return f"I understand, {conv['lead_info'].get('name', '')}. Thank you for your time. Feel free to reach out if anything changes. Have a great day!"
        else:
            return f"Great talking with you! I'll send you the details we discussed. Feel free to call me anytime. Thanks, and have a wonderful day!"
    
    def get_conversation_stats(self, call_sid: str) -> Dict[str, Any]:
        """Get conversation statistics"""
        if call_sid not in self.conversations:
            return {}
        
        conv = self.conversations[call_sid]
        history = conv["conversation_history"]
        
        return {
            "call_sid": call_sid,
            "call_type": conv["call_type"],
            "duration_exchanges": len(history) // 2,
            "final_sentiment": conv["context"]["customer_sentiment"],
            "stage_reached": conv["context"]["stage"],
            "key_information": conv["context"]["key_information"]
        }
