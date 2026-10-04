import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class ConversationAI:
    """
    Human-like AI that makes sales calls and converts leads naturally.
    Showcases Murf AI's premium voice synthesis for realistic conversations.
    """
    
    def __init__(self, azure_service, murf_service, websocket_manager):
        self.azure_service = azure_service
        self.murf_service = murf_service
        self.websocket_manager = websocket_manager
        self.logger = logging.getLogger(__name__)
        
        # Conversation state tracking
        self.active_conversations: Dict[str, Dict] = {}
        
        # Voice personas optimized for Murf AI
        self.voice_personas = {
            "b2b_sales": {
                "name": "Alex Thompson",
                "role": "Senior Sales Executive",
                "murf_voice": "en-US-terrell",  # Professional American male voice
                "personality": "confident, consultative, solution-focused",
                "speaking_rate": 1.0,
                "pitch": 0,
                "energy": "medium-high"
            },
            "real_estate": {
                "name": "Priya Sharma",
                "role": "Property Consultant",
                "murf_voice": "en-US-natalie",  # Friendly American female voice
                "personality": "warm, knowledgeable, trustworthy",
                "speaking_rate": 0.95,
                "pitch": 5,
                "energy": "medium"
            }
        }
        
        self.logger.info("Conversation AI initialized with Murf voice personas")
    
    async def start_outbound_call(
        self, 
        session_id: str, 
        call_type: str,
        lead_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Start an outbound call (B2B sales or real estate lead)
        This is the main demo function showing Murf AI's capabilities
        """
        
        self.logger.info(f"Starting {call_type} call for session {session_id}")
        
        # Select appropriate persona
        persona = self.voice_personas.get(call_type, self.voice_personas["b2b_sales"])
        
        # Initialize conversation state
        self.active_conversations[session_id] = {
            "call_type": call_type,
            "persona": persona,
            "lead_info": lead_info,
            "conversation_stage": "opening",
            "messages": [],
            "started_at": datetime.now().isoformat(),
            "engagement_score": 0
        }
        
        # Generate natural opening with Murf AI
        opening_script = await self._generate_opening_script(call_type, lead_info, persona)
        
        # Convert to premium voice using Murf AI
        voice_audio = await self._generate_murf_voice(
            opening_script["text"],
            persona,
            emotion="friendly"
        )
        
        # Log the interaction
        self.logger.info(f"Call started - {persona['name']} calling {lead_info.get('name', 'prospect')}")
        
        return {
            "session_id": session_id,
            "status": "call_started",
            "persona": persona,
            "opening_message": opening_script,
            "voice_audio": voice_audio,
            "next_action": "wait_for_response"
        }
    
    async def _generate_opening_script(
        self, 
        call_type: str, 
        lead_info: Dict[str, Any],
        persona: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate natural opening script based on call type"""
        
        lead_name = lead_info.get("name", "there")
        company = lead_info.get("company", "")
        
        if call_type == "b2b_sales":
            # B2B Sales Opening - Professional and value-focused
            opening_text = f"""
            Hi {lead_name}, this is {persona['name']} from our sales team. 
            I hope I'm catching you at a good time?
            
            I'm calling because I noticed your company, {company}, has been growing rapidly, 
            and I wanted to share how we've helped similar businesses in your industry 
            increase their efficiency by 40% on average.
            
            I know your time is valuable, so I'll keep this brief. 
            Could we take just 5 minutes to explore if this might be relevant for you?
            """.strip()
            
        else:  # real_estate
            # Real Estate Opening - Warm and consultative
            property_type = lead_info.get("interested_in", "property")
            opening_text = f"""
            Hello {lead_name}! This is {persona['name']} calling from our real estate team.
            How are you doing today?
            
            I'm reaching out because I saw you were interested in {property_type} properties,
            and I actually have some excellent options that just became available 
            that match exactly what you're looking for.
            
            Do you have a couple of minutes to discuss what you're looking for in your dream home?
            """.strip()
        
        return {
            "text": opening_text,
            "intent": "build_rapport",
            "expected_responses": ["yes", "not_now", "tell_me_more"]
        }
    
    async def _generate_murf_voice(
        self,
        text: str,
        persona: Dict[str, Any],
        emotion: str = "neutral"
    ) -> Dict[str, Any]:
        """
        Generate premium voice using Murf AI with emotion and personality.
        This showcases Murf's advanced voice synthesis capabilities.
        """
        
        try:
            # Add natural pauses and emphasis for human-like delivery
            enhanced_text = self._add_natural_speech_patterns(text)
            
            # Generate with Murf AI premium voice
            audio_result = await self.murf_service.generate_speech(
                text=enhanced_text,
                voice_id=persona["murf_voice"],
                style={
                    "speaking_rate": persona["speaking_rate"],
                    "pitch": persona["pitch"],
                    "emotion": emotion
                }
            )
            
            self.logger.info(f"Generated Murf voice: {len(text)} chars, emotion={emotion}")
            
            return {
                "audio_data": audio_result.get("audio_data"),
                "duration_ms": audio_result.get("duration_ms", 0),
                "voice_id": persona["murf_voice"],
                "text": text
            }
            
        except Exception as e:
            self.logger.error(f"Murf voice generation error: {e}")
            # Fallback to basic synthesis
            return await self.murf_service.generate_speech(text, persona["murf_voice"])
    
    def _add_natural_speech_patterns(self, text: str) -> str:
        """Add natural pauses and emphasis for human-like speech"""
        
        # Add pauses at commas and periods for natural rhythm
        text = text.replace(",", ", <break time='300ms'/>")
        text = text.replace(".", ". <break time='500ms'/>")
        text = text.replace("?", "? <break time='400ms'/>")
        
        # Add emphasis on key words
        emphasis_words = ["increase", "save", "improve", "exclusive", "perfect", "excellent"]
        for word in emphasis_words:
            text = text.replace(word, f"<emphasis level='strong'>{word}</emphasis>")
        
        return text
    
    async def handle_prospect_response(
        self,
        session_id: str,
        prospect_message: str,
        audio_data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Handle prospect's response and generate intelligent follow-up.
        This is where the AI shows its conversational intelligence.
        """
        
        if session_id not in self.active_conversations:
            self.logger.warning(f"No active conversation for session {session_id}")
            return {"error": "No active conversation"}
        
        conversation = self.active_conversations[session_id]
        persona = conversation["persona"]
        call_type = conversation["call_type"]
        
        # Store prospect message
        conversation["messages"].append({
            "speaker": "prospect",
            "text": prospect_message,
            "timestamp": datetime.now().isoformat()
        })
        
        self.logger.info(f"Prospect response: {prospect_message[:50]}...")
        
        # Analyze response sentiment and intent
        analysis = await self._analyze_prospect_response(prospect_message, call_type)
        
        # Update conversation stage
        conversation["conversation_stage"] = analysis["next_stage"]
        conversation["engagement_score"] = analysis["engagement_score"]
        
        # Generate intelligent response
        ai_response = await self._generate_intelligent_response(
            analysis,
            conversation,
            persona
        )
        
        # Convert to Murf voice with appropriate emotion
        voice_audio = await self._generate_murf_voice(
            ai_response["text"],
            persona,
            emotion=ai_response["emotion"]
        )
        
        # Store AI response
        conversation["messages"].append({
            "speaker": "ai",
            "text": ai_response["text"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Send real-time update via WebSocket
        await self._broadcast_conversation_update(session_id, {
            "type": "ai_response",
            "text": ai_response["text"],
            "emotion": ai_response["emotion"],
            "stage": conversation["conversation_stage"]
        })
        
        return {
            "status": "response_generated",
            "ai_response": ai_response,
            "voice_audio": voice_audio,
            "conversation_stage": conversation["conversation_stage"],
            "engagement_score": conversation["engagement_score"],
            "next_action": ai_response["next_action"]
        }
    
    async def _analyze_prospect_response(
        self,
        message: str,
        call_type: str
    ) -> Dict[str, Any]:
        """Analyze prospect's response using Azure OpenAI"""
        
        analysis_prompt = f"""
        Analyze this prospect's response in a {call_type} call:
        
        Prospect said: "{message}"
        
        Determine:
        1. Sentiment (positive/neutral/negative)
        2. Intent (interested/objection/question/not_interested)
        3. Engagement level (1-10)
        4. Key concerns or interests mentioned
        5. Next conversation stage (discovery/presentation/objection_handling/closing)
        6. Buying signals (yes/no)
        
        Return as JSON.
        """
        
        try:
            # Convert to message array format and use correct method name
            messages = [
                {"role": "system", "content": "You are a sales conversation analyzer. Return only valid JSON format."},
                {"role": "user", "content": analysis_prompt}
            ]
            result = await self.azure_service.generate_text(
                messages,
                max_tokens=200,
                temperature=0.3
            )
            
            # Parse JSON from result
            analysis = json.loads(result)
            
            return {
                "sentiment": analysis.get("sentiment", "neutral"),
                "intent": analysis.get("intent", "question"),
                "engagement_score": analysis.get("engagement_level", 5),
                "key_points": analysis.get("key_concerns", []),
                "next_stage": analysis.get("next_conversation_stage", "discovery"),
                "buying_signals": analysis.get("buying_signals", False)
            }
            
        except Exception as e:
            self.logger.error(f"Response analysis error: {e}")
            # Fallback to simple analysis
            return self._simple_sentiment_analysis(message)
    
    def _simple_sentiment_analysis(self, message: str) -> Dict[str, Any]:
        """Simple fallback sentiment analysis"""
        
        message_lower = message.lower()
        
        # Positive signals
        positive_words = ["yes", "interested", "sounds good", "tell me more", "great", "perfect"]
        # Negative signals
        negative_words = ["no", "not interested", "busy", "expensive", "not now"]
        # Question signals
        question_words = ["how", "what", "when", "why", "can you", "tell me"]
        
        if any(word in message_lower for word in positive_words):
            sentiment = "positive"
            intent = "interested"
            engagement = 8
        elif any(word in message_lower for word in negative_words):
            sentiment = "negative"
            intent = "objection"
            engagement = 3
        elif any(word in message_lower for word in question_words):
            sentiment = "neutral"
            intent = "question"
            engagement = 6
        else:
            sentiment = "neutral"
            intent = "question"
            engagement = 5
        
        return {
            "sentiment": sentiment,
            "intent": intent,
            "engagement_score": engagement,
            "key_points": [],
            "next_stage": "discovery" if engagement > 5 else "objection_handling",
            "buying_signals": engagement > 7
        }
    
    async def _generate_intelligent_response(
        self,
        analysis: Dict[str, Any],
        conversation: Dict[str, Any],
        persona: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate contextual, intelligent response based on analysis"""
        
        call_type = conversation["call_type"]
        sentiment = analysis["sentiment"]
        intent = analysis["intent"]
        stage = analysis["next_stage"]
        
        # Response strategies based on intent
        if intent == "interested":
            response = await self._generate_discovery_response(call_type, conversation, persona)
            emotion = "enthusiastic"
            next_action = "present_value"
            
        elif intent == "objection":
            response = await self._handle_objection(analysis, call_type, persona)
            emotion = "understanding"
            next_action = "address_concern"
            
        elif intent == "question":
            response = await self._answer_question(analysis, call_type, persona)
            emotion = "helpful"
            next_action = "provide_info"
            
        elif intent == "not_interested":
            response = await self._soft_close(call_type, persona)
            emotion = "professional"
            next_action = "schedule_followup"
            
        else:
            response = await self._keep_conversation_flowing(stage, call_type, persona)
            emotion = "neutral"
            next_action = "continue_discovery"
        
        return {
            "text": response,
            "emotion": emotion,
            "next_action": next_action,
            "confidence": 0.8
        }
    
    async def _generate_discovery_response(
        self,
        call_type: str,
        conversation: Dict[str, Any],
        persona: Dict[str, Any]
    ) -> str:
        """Generate discovery questions to understand needs"""
        
        if call_type == "b2b_sales":
            return f"""
            Fantastic! I'm glad you're interested.
            
            To make sure I show you the most relevant solutions, 
            let me ask you a couple of quick questions.
            
            What are the top two challenges your team is facing right now 
            when it comes to productivity or efficiency?
            """.strip()
        
        else:  # real_estate
            return f"""
            Wonderful! I'm excited to help you find your perfect home.
            
            Let me understand your needs better. 
            What's most important to you - location, budget, or specific amenities?
            
            And are you looking to move in immediately, or do you have some flexibility with timing?
            """.strip()
    
    async def _handle_objection(
        self,
        analysis: Dict[str, Any],
        call_type: str,
        persona: Dict[str, Any]
    ) -> str:
        """Handle objections professionally"""
        
        if call_type == "b2b_sales":
            return """
            I completely understand your concern, and I appreciate you being upfront about it.
            
            Many of our clients initially felt the same way, but what they found was that 
            the ROI actually paid for itself within the first quarter.
            
            What if I could show you a quick case study from a company similar to yours 
            that was in the exact same situation? Would that be helpful?
            """.strip()
        
        else:  # real_estate
            return """
            I totally understand where you're coming from, and that's a valid concern.
            
            What I can do is show you some options that fit different budget ranges, 
            and we can explore flexible payment plans that many of our clients find comfortable.
            
            Would you be open to seeing a few properties this weekend? 
            No commitment, just to get a better sense of what's available.
            """.strip()
    
    async def _answer_question(
        self,
        analysis: Dict[str, Any],
        call_type: str,
        persona: Dict[str, Any]
    ) -> str:
        """Answer prospect questions directly"""
        
        return """
        That's a great question! Let me address that directly.
        
        [Specific answer based on the question]
        
        Does that answer your question, or would you like me to dive deeper into any specific aspect?
        """.strip()
    
    async def _soft_close(self, call_type: str, persona: Dict[str, Any]) -> str:
        """Soft close when prospect is not interested"""
        
        return f"""
        I completely understand, and I respect your time.
        
        Let me leave you with my direct contact information - 
        if anything changes or if you'd like to revisit this conversation, 
        feel free to reach out anytime.
        
        Can I at least send you a quick email with some information 
        that you can review when you have time?
        """.strip()
    
    async def _keep_conversation_flowing(
        self,
        stage: str,
        call_type: str,
        persona: Dict[str, Any]
    ) -> str:
        """Keep the conversation natural and flowing"""
        
        return """
        I appreciate you sharing that with me.
        
        Based on what you've told me, I think we have some solutions 
        that could really make a difference for you.
        
        Can we schedule a quick 15-minute demo call later this week 
        where I can show you exactly how this works?
        """.strip()
    
    async def _broadcast_conversation_update(
        self,
        session_id: str,
        update: Dict[str, Any]
    ):
        """Send real-time updates via WebSocket"""
        
        try:
            await self.websocket_manager.send_message(session_id, {
                "type": "conversation_update",
                "data": update,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            self.logger.warning(f"Failed to broadcast update: {e}")
    
    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get complete conversation summary for demo purposes"""
        
        if session_id not in self.active_conversations:
            return {"error": "Conversation not found"}
        
        conversation = self.active_conversations[session_id]
        
        return {
            "session_id": session_id,
            "call_type": conversation["call_type"],
            "persona": conversation["persona"]["name"],
            "duration": "N/A",  # Calculate from timestamps
            "engagement_score": conversation["engagement_score"],
            "conversation_stage": conversation["conversation_stage"],
            "message_count": len(conversation["messages"]),
            "messages": conversation["messages"],
            "lead_info": conversation["lead_info"],
            "outcome": self._determine_call_outcome(conversation)
        }
    
    def _determine_call_outcome(self, conversation: Dict[str, Any]) -> str:
        """Determine the outcome of the call"""
        
        engagement = conversation["engagement_score"]
        stage = conversation["conversation_stage"]
        
        if engagement >= 8:
            return "high_interest"
        elif engagement >= 6:
            return "moderate_interest"
        elif stage == "objection_handling":
            return "needs_followup"
        else:
            return "low_interest"
    
    async def close_conversation(self, session_id: str) -> Dict[str, Any]:
        """Close and archive conversation"""
        
        if session_id in self.active_conversations:
            summary = await self.get_conversation_summary(session_id)
            
            # Archive the conversation
            archived = self.active_conversations.pop(session_id)
            
            self.logger.info(f"Conversation closed: {session_id}, outcome: {summary['outcome']}")
            
            return {
                "status": "closed",
                "summary": summary
            }
        
        return {"error": "Conversation not found"}
