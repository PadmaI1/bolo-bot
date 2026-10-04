import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time

class RealEstateAIEngine:
    """Advanced AI engine for real estate lead qualification and property matching"""
    
    def __init__(self, azure_service, murf_service, websocket_manager):
        self.azure_service = azure_service
        self.murf_service = murf_service
        self.websocket_manager = websocket_manager
        self.logger = logging.getLogger(__name__)
        
        # Active real estate sessions
        self.active_sessions = {}
        
        # Lead qualification framework
        self.qualification_criteria = {
            "essential_info": {
                "budget_range": {
                    "weight": 25,
                    "questions": [
                        "What budget range are you considering?",
                        "Have you been pre-approved for a home loan?",
                        "What EMI range would be comfortable for you?"
                    ]
                },
                "property_type": {
                    "weight": 20,
                    "questions": [
                        "What type of property are you looking for?",
                        "Are you interested in apartments or independent houses?",
                        "Any specific configuration preferences?"
                    ]
                },
                "location": {
                    "weight": 20,
                    "questions": [
                        "Which areas are you considering?",
                        "What's important to you about the location?",
                        "Do you have workplace or school proximity requirements?"
                    ]
                },
                "timeline": {
                    "weight": 15,
                    "questions": [
                        "When are you planning to make this purchase?",
                        "Is this urgent or can you wait for the right property?",
                        "When would you like to move in?"
                    ]
                },
                "purpose": {
                    "weight": 10,
                    "questions": [
                        "Is this for your own use or investment?",
                        "Are you upgrading or first-time buying?",
                        "Any specific requirements from family members?"
                    ]
                },
                "financing": {
                    "weight": 10,
                    "questions": [
                        "How do you plan to finance this purchase?",
                        "Do you need help with home loan processes?",
                        "Any specific bank preferences?"
                    ]
                }
            }
        }
        
        # Market intelligence data
        self.market_insights = {
            "bangalore": {
                "avg_appreciation": "8-12% annually",
                "hot_areas": ["Whitefield", "Electronic City", "Sarjapur", "Hebbal"],
                "price_ranges": {
                    "entry_level": "40-80 lakhs",
                    "mid_segment": "80-150 lakhs", 
                    "premium": "150-300 lakhs"
                },
                "rental_yields": "2.5-4.0%",
                "infrastructure_projects": ["Metro Phase 3", "Peripheral Ring Road", "IT Parks Expansion"]
            },
            "gurgaon": {
                "avg_appreciation": "6-10% annually",
                "hot_areas": ["Sector 70-80", "New Gurgaon", "Golf Course Extension", "Sohna Road"],
                "price_ranges": {
                    "entry_level": "60-120 lakhs",
                    "mid_segment": "120-250 lakhs",
                    "premium": "250-500 lakhs"
                },
                "rental_yields": "2.0-3.5%",
                "infrastructure_projects": ["Dwarka Expressway", "Metro Expansion", "Commercial Hubs"]
            }
        }
        
        # Conversation flow patterns
        self.conversation_patterns = {
            "greeting_responses": {
                "english": [
                    "Hello! Thank you for your interest in properties. I'm here to help you find the perfect home.",
                    "Hi! I understand you're looking for a property. Let me help you find the best options.",
                    "Welcome! I'm excited to help you with your property search. Let's get started."
                ],
                "hindi": [
                    "नमस्ते! प्रॉपर्टी में आपकी रुचि के लिए धन्यवाद। मैं आपको सबसे अच्छा घर खोजने में मदद करूंगा।",
                    "हैलो! मैं समझता हूं कि आप एक प्रॉपर्टी की तलाश कर रहे हैं। आइए सबसे अच्छे विकल्प खोजते हैं।",
                    "आपका स्वागत है! मैं आपकी प्रॉपर्टी खोज में मदद करने के लिए उत्साहित हूं।"
                ]
            },
            "objection_responses": {
                "price_objection": {
                    "english": "I understand budget is important. Let me show you the long-term value and payment options available.",
                    "hindi": "मैं समझता हूं कि बजट महत्वपूर्ण है। मैं आपको दीर्घकालिक मूल्य और उपलब्ध भुगतान विकल्प दिखाता हूं।"
                },
                "location_concern": {
                    "english": "Location is crucial. Let me explain the connectivity and future development plans for this area.",
                    "hindi": "स्थान बहुत महत्वपूर्ण है। मैं इस क्षेत्र की कनेक्टिविटी और भविष्य की विकास योजनाओं के बारे में बताता हूं।"
                },
                "timing_hesitation": {
                    "english": "Timing is important. However, property prices are increasing. Let me show you how to secure this at today's price.",
                    "hindi": "समय महत्वपूर्ण है। लेकिन प्रॉपर्टी की कीमतें बढ़ रही हैं। मैं आपको दिखाता हूं कि आज की कीमत पर इसे कैसे सुरक्षित करें।"
                }
            }
        }
    
    async def initialize_realestate_session(self, session_id: str, lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize real estate qualification session"""
        try:
            self.active_sessions[session_id] = {
                "session_id": session_id,
                "start_time": datetime.now(),
                "lead_context": lead_context,
                "conversation_history": [],
                "qualification_data": {
                    "budget_range": None,
                    "property_type": None,
                    "locations": [],
                    "timeline": None,
                    "purpose": None,
                    "financing_status": None,
                    "family_requirements": [],
                    "amenities_preferred": [],
                    "concerns_objections": []
                },
                "qualification_score": 0,
                "completion_percentage": 0,
                "language_preference": lead_context.get("language", "english"),
                "engagement_metrics": {
                    "questions_answered": 0,
                    "enthusiasm_level": 5,
                    "objection_count": 0,
                    "positive_responses": 0
                },
                "property_matches": [],
                "next_best_action": "start_qualification",
                "ai_insights": []
            }
            
            # Generate welcome message
            welcome_response = await self._generate_welcome_message(session_id)
            
            return {
                "status": "success",
                "session_id": session_id,
                "welcome_message": welcome_response,
                "qualification_framework": list(self.qualification_criteria["essential_info"].keys()),
                "language": self.active_sessions[session_id]["language_preference"]
            }
            
        except Exception as e:
            self.logger.error(f"Real estate session initialization error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def process_realestate_conversation(self, session_id: str, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process real estate conversation and provide intelligent responses"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        try:
            session = self.active_sessions[session_id]
            transcript_text = transcript_data.get("text", "")
            speaker = transcript_data.get("speaker_detected", "customer")
            
            # Add to conversation history
            conversation_entry = {
                "timestamp": datetime.now().isoformat(),
                "speaker": speaker,
                "text": transcript_text,
                "confidence": transcript_data.get("confidence", 0.8)
            }
            session["conversation_history"].append(conversation_entry)
            
            # Update engagement metrics
            await self._update_engagement_metrics(session, conversation_entry)
            
            # Build conversation context for AI analysis
            conversation_context = self._build_conversation_context(session)
            
            # Analyze with Azure AI
            analysis_result = await self.azure_service.analyze_conversation_advanced(
                transcript_text,
                "real_estate",
                {
                    "session_context": session["lead_context"],
                    "conversation_history": conversation_context,
                    "qualification_progress": session["qualification_data"],
                    "language_preference": session["language_preference"],
                    "current_completion": session["completion_percentage"]
                }
            )
            
            # Update qualification data based on analysis
            await self._update_qualification_data(session, analysis_result)
            
            # Generate AI response strategy
            response_strategy = await self._generate_response_strategy(session, analysis_result)
            
            # Generate voice response if needed
            if response_strategy.get("generate_voice_response"):
                voice_response = await self._generate_voice_response(session, response_strategy)
                response_strategy["voice_audio"] = voice_response
            
            # Check for property matching trigger
            if session["completion_percentage"] >= 60:
                property_matches = await self._find_property_matches(session)
                response_strategy["property_matches"] = property_matches
            
            # Update session state
            await self._update_session_state(session, analysis_result, response_strategy)
            
            return {
                "session_id": session_id,
                "analysis": analysis_result,
                "qualification_update": session["qualification_data"],
                "completion_percentage": session["completion_percentage"],
                "qualification_score": session["qualification_score"],
                "response_strategy": response_strategy,
                "engagement_metrics": session["engagement_metrics"],
                "next_best_action": session["next_best_action"]
            }
            
        except Exception as e:
            self.logger.error(f"Real estate conversation processing error: {e}")
            return {"error": str(e)}
    
    async def _generate_welcome_message(self, session_id: str) -> Dict[str, Any]:
        """Generate personalized welcome message"""
        session = self.active_sessions[session_id]
        language = session["language_preference"]
        lead_name = session["lead_context"].get("name", "Customer")
        
        # Select appropriate welcome message
        welcome_texts = self.conversation_patterns["greeting_responses"][language]
        welcome_text = welcome_texts[0]  # Use first option for consistency
        
        # Personalize the message
        if lead_name and lead_name != "Customer":
            if language == "hindi":
                welcome_text = f"नमस्ते {lead_name} जी! " + welcome_text
            else:
                welcome_text = f"Hello {lead_name}! " + welcome_text
        
        # Generate voice welcome
        voice_profile = "hindi_property_agent_female" if language == "hindi" else "realestate_consultant_female"
        welcome_audio = await self.murf_service.generate_premium_voice(welcome_text, voice_profile)
        
        return {
            "text": welcome_text,
            "audio": welcome_audio,
            "language": language,
            "type": "welcome"
        }
    
    async def _update_engagement_metrics(self, session: Dict[str, Any], conversation_entry: Dict[str, Any]):
        """Update real-time engagement metrics"""
        speaker = conversation_entry["speaker"]
        text = conversation_entry["text"].lower()
        metrics = session["engagement_metrics"]
        
        if speaker == "customer":
            # Count questions answered
            if any(indicator in text for indicator in ["yes", "no", "maybe", "sure", "okay", "नहीं", "हां"]):
                metrics["questions_answered"] += 1
            
            # Detect positive responses
            positive_indicators = ["great", "good", "excellent", "perfect", "interested", "like", "love", "बहुत अच्छा", "अच्छा"]
            if any(indicator in text for indicator in positive_indicators):
                metrics["positive_responses"] += 1
                metrics["enthusiasm_level"] = min(10, metrics["enthusiasm_level"] + 0.5)
            
            # Detect objections or concerns
            objection_indicators = ["expensive", "costly", "budget", "concern", "worried", "not sure", "महंगा", "चिंता"]
            if any(indicator in text for indicator in objection_indicators):
                metrics["objection_count"] += 1
                metrics["enthusiasm_level"] = max(1, metrics["enthusiasm_level"] - 0.3)
    
    def _build_conversation_context(self, session: Dict[str, Any]) -> str:
        """Build conversation context for AI analysis"""
        recent_messages = session["conversation_history"][-8:]  # Last 8 messages
        context_parts = []
        
        for msg in recent_messages:
            speaker_label = "Agent" if msg["speaker"] == "agent" else "Customer"
            context_parts.append(f"{speaker_label}: {msg['text']}")
        
        return "\n".join(context_parts)
    
    async def _update_qualification_data(self, session: Dict[str, Any], analysis: Dict[str, Any]):
        """Update qualification data based on AI analysis"""
        qual_data = session["qualification_data"]
        
        if "customer_profile" in analysis:
            profile = analysis["customer_profile"]
            
            # Update budget information
            if profile.get("budget_range") and profile["budget_range"] != "not_disclosed":
                qual_data["budget_range"] = profile["budget_range"]
            
            # Update buyer type/purpose
            if profile.get("buyer_type"):
                qual_data["purpose"] = profile["buyer_type"]
            
            # Update timeline
            if profile.get("decision_timeline"):
                qual_data["timeline"] = profile["decision_timeline"]
            
            # Update financing status
            if profile.get("financing_status"):
                qual_data["financing_status"] = profile["financing_status"]
        
        if "property_requirements" in analysis:
            requirements = analysis["property_requirements"]
            
            # Update property type
            if requirements.get("property_type") != "flexible":
                qual_data["property_type"] = requirements["property_type"]
            
            # Update location preferences
            if requirements.get("location_preferences") and requirements["location_preferences"] != ["any"]:
                qual_data["locations"] = list(set(qual_data["locations"] + requirements["location_preferences"]))
            
            # Update amenities
            if requirements.get("key_amenities_wanted"):
                qual_data["amenities_preferred"] = list(set(qual_data["amenities_preferred"] + requirements["key_amenities_wanted"]))
        
        if "conversation_insights" in analysis:
            insights = analysis["conversation_insights"]
            
            # Update concerns
            if insights.get("concerns_objections"):
                qual_data["concerns_objections"] = list(set(qual_data["concerns_objections"] + insights["concerns_objections"]))
        
        # Calculate completion percentage and qualification score
        await self._calculate_qualification_metrics(session)
    
    async def _calculate_qualification_metrics(self, session: Dict[str, Any]):
        """Calculate qualification score and completion percentage"""
        qual_data = session["qualification_data"]
        criteria = self.qualification_criteria["essential_info"]
        
        total_weight = sum(criterion["weight"] for criterion in criteria.values())
        completed_weight = 0
        qualification_points = 0
        
        for field, criterion in criteria.items():
            field_value = qual_data.get(field.replace("_", "_"))  # Handle field name mapping
            
            if field == "budget_range" and qual_data.get("budget_range"):
                completed_weight += criterion["weight"]
                qualification_points += criterion["weight"] * 1.0  # Full points for budget
            elif field == "property_type" and qual_data.get("property_type"):
                completed_weight += criterion["weight"]
                qualification_points += criterion["weight"] * 1.0
            elif field == "location" and qual_data.get("locations"):
                completed_weight += criterion["weight"]
                qualification_points += criterion["weight"] * 1.0
            elif field == "timeline" and qual_data.get("timeline"):
                completed_weight += criterion["weight"]
                # Higher points for more urgent timelines
                urgency_multiplier = {"immediate": 1.0, "1-3months": 0.9, "3-6months": 0.7, "exploring": 0.5}
                multiplier = urgency_multiplier.get(qual_data["timeline"], 0.6)
                qualification_points += criterion["weight"] * multiplier
            elif field == "purpose" and qual_data.get("purpose"):
                completed_weight += criterion["weight"]
                qualification_points += criterion["weight"] * 1.0
            elif field == "financing" and qual_data.get("financing_status"):
                completed_weight += criterion["weight"]
                # Higher points for pre-approved or cash buyers
                financing_multiplier = {"cash_buyer": 1.0, "pre_approved": 0.9, "loan_required": 0.7, "exploring_options": 0.5}
                multiplier = financing_multiplier.get(qual_data["financing_status"], 0.6)
                qualification_points += criterion["weight"] * multiplier
        
        # Calculate percentages
        completion_percentage = (completed_weight / total_weight) * 100
        qualification_score = min(10, (qualification_points / total_weight) * 10)
        
        # Apply engagement bonus/penalty
        engagement_level = session["engagement_metrics"]["enthusiasm_level"]
        engagement_bonus = (engagement_level - 5) * 0.5  # +/- 2.5 points max
        qualification_score = max(0, min(10, qualification_score + engagement_bonus))
        
        # Update session
        session["completion_percentage"] = round(completion_percentage, 1)
        session["qualification_score"] = round(qualification_score, 1)
    
    async def _generate_response_strategy(self, session: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent response strategy"""
        strategy = {
            "response_type": "continue_qualification",
            "priority_questions": [],
            "response_text": "",
            "generate_voice_response": True,
            "urgency": "medium",
            "next_steps": []
        }
        
        completion = session["completion_percentage"]
        score = session["qualification_score"]
        
        # Determine response based on completion and analysis
        if completion < 40:
            # Early stage - focus on essential information
            strategy["response_type"] = "gather_essentials"
            strategy["priority_questions"] = self._get_missing_essential_questions(session)
            strategy["response_text"] = self._generate_qualification_question(session, strategy["priority_questions"][0] if strategy["priority_questions"] else None)
        
        elif completion >= 40 and completion < 80:
            # Mid stage - deep dive and clarification
            strategy["response_type"] = "detailed_qualification"
            
            # Check for immediate actions from analysis
            if analysis.get("next_actions", {}).get("immediate_priority") == "send_properties":
                strategy["response_type"] = "property_recommendation"
                strategy["response_text"] = self._generate_property_sharing_response(session)
            elif analysis.get("next_actions", {}).get("immediate_priority") == "schedule_visit":
                strategy["response_type"] = "site_visit_scheduling"
                strategy["response_text"] = self._generate_site_visit_response(session)
            else:
                # Continue with detailed questions
                strategy["priority_questions"] = self._get_detailed_questions(session, analysis)
                strategy["response_text"] = self._generate_qualification_question(session, strategy["priority_questions"][0] if strategy["priority_questions"] else None)
        
        else:
            # High completion - move to action
            if score >= 7:
                strategy["response_type"] = "schedule_site_visit"
                strategy["urgency"] = "high"
                strategy["response_text"] = self._generate_site_visit_response(session)
                strategy["next_steps"] = ["Schedule site visit", "Send property details", "Prepare documents"]
            elif score >= 5:
                strategy["response_type"] = "send_properties"
                strategy["response_text"] = self._generate_property_sharing_response(session)
                strategy["next_steps"] = ["Send property portfolio", "Schedule follow-up call"]
            else:
                strategy["response_type"] = "nurture_lead"
                strategy["response_text"] = self._generate_nurture_response(session)
                strategy["next_steps"] = ["Add to nurture campaign", "Send market updates"]
        
        # Handle objections if detected
        if analysis.get("conversation_insights", {}).get("concerns_objections"):
            objection_response = await self._generate_objection_response(session, analysis)
            if objection_response:
                strategy["objection_handling"] = objection_response
                strategy["response_text"] = objection_response["response_text"]
                strategy["urgency"] = "high"
        
        return strategy
    
    def _get_missing_essential_questions(self, session: Dict[str, Any]) -> List[str]:
        """Get priority questions for missing essential information"""
        qual_data = session["qualification_data"]
        criteria = self.qualification_criteria["essential_info"]
        missing_questions = []
        
        # Prioritize by weight (highest weight first)
        sorted_criteria = sorted(criteria.items(), key=lambda x: x[1]["weight"], reverse=True)
        
        for field, criterion in sorted_criteria:
            field_value = qual_data.get(field)
            
            if not field_value or (isinstance(field_value, list) and not field_value):
                # Select best question based on context
                missing_questions.extend(criterion["questions"][:1])  # Take first question
        
        return missing_questions[:2]  # Return top 2 priority questions
    
    def _generate_qualification_question(self, session: Dict[str, Any], question: str) -> str:
        """Generate contextual qualification question"""
        if not question:
            return "Tell me more about your ideal property."
        
        language = session["language_preference"]
        
        if language == "hindi":
            # Simple translation mapping for common questions
            hindi_translations = {
                "What budget range are you considering?": "आप किस बजट रेंज पर विचार कर रहे हैं?",
                "What type of property are you looking for?": "आप किस प्रकार की संपत्ति की तलाश कर रहे हैं?",
                "Which areas are you considering?": "आप किन क्षेत्रों पर विचार कर रहे हैं?",
                "When are you planning to make this purchase?": "आप इस खरीदारी की योजना कब बना रहे हैं?",
                "Is this for your own use or investment?": "क्या यह आपके अपने उपयोग के लिए है या निवेश के लिए?"
            }
            question = hindi_translations.get(question, question)
        
        return question
    
    def _generate_property_sharing_response(self, session: Dict[str, Any]) -> str:
        """Generate property sharing response"""
        language = session["language_preference"]
        
        if language == "hindi":
            return """
            बहुत अच्छा! आपकी आवश्यकताओं के आधार पर, मेरे पास कुछ बेहतरीन प्रॉपर्टीज हैं जो आपके बजट और पसंद के अनुकूल हैं।
            
            मैं आपको विस्तृत जानकारी भेजूंगा जिसमें फ्लोर प्लान, कीमत, भुगतान योजनाएं और उच्च गुणवत्ता की तस्वीरें शामिल हैं।
            
            क्या मैं आपको व्हाट्सऐप पर ये विवरण भेज सकता हूं?
            """
        else:
            return """
            Perfect! Based on your requirements, I have some excellent properties that match your budget and preferences.
            
            I'll send you complete details including floor plans, pricing, payment schemes, and high-resolution photos.
            
            Can I share these property details on your WhatsApp number?
            """
    
    def _generate_site_visit_response(self, session: Dict[str, Any]) -> str:
        """Generate site visit scheduling response"""
        language = session["language_preference"]
        
        if language == "hindi":
            return """
            यह शानदार है! आपकी आवश्यकताएं इस संपत्ति के साथ बिल्कुल मेल खाती हैं।
            
            क्या आप इस सप्ताहांत साइट विजिट के लिए उपलब्ध हैं? मैं आपके सुविधाजनक समय पर इसकी व्यवस्था कर सकता हूं।
            
            हमारे प्रॉपर्टी कंसल्टेंट आपको पूरी जानकारी के साथ प्रॉपर्टी दिखाएंगे।
            """
        else:
            return """
            Excellent! Your requirements align perfectly with this property.
            
            Would you be available for a site visit this weekend? I can arrange it at your convenient time.
            
            Our property consultant will give you a complete walkthrough with all the details.
            """
    
    async def _generate_objection_response(self, session: Dict[str, Any], analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate response for customer objections"""
        objections = analysis.get("conversation_insights", {}).get("concerns_objections", [])
        if not objections:
            return None
        
        # Categorize the objection
        objection_type = self._categorize_objection(objections[0])
        language = session["language_preference"]
        
        response_templates = self.conversation_patterns["objection_responses"]
        response_text = response_templates.get(objection_type, {}).get(language, "")
        
        if not response_text:
            # Fallback response
            if language == "hindi":
                response_text = "मैं आपकी चिंता समझ सकता हूं। आइए इस बारे में विस्तार से बात करते हैं।"
            else:
                response_text = "I understand your concern. Let me address that for you."
        
        return {
            "objection_type": objection_type,
            "response_text": response_text,
            "priority": "high"
        }
    
    def _categorize_objection(self, objection: str) -> str:
        """Categorize customer objection"""
        objection_lower = objection.lower()
        
        if any(word in objection_lower for word in ["price", "expensive", "cost", "budget", "महंगा"]):
            return "price_objection"
        elif any(word in objection_lower for word in ["location", "area", "far", "distance", "स्थान"]):
            return "location_concern"
        elif any(word in objection_lower for word in ["time", "timing", "wait", "later", "समय"]):
            return "timing_hesitation"
        else:
            return "general_concern"
    
    async def _generate_voice_response(self, session: Dict[str, Any], strategy: Dict[str, Any]) -> Optional[bytes]:
        """Generate voice response using Murf AI"""
        try:
            response_text = strategy.get("response_text", "")
            if not response_text:
                return None
            
            language = session["language_preference"]
            voice_profile = "hindi_property_agent_female" if language == "hindi" else "realestate_consultant_female"
            
            # Generate voice with appropriate settings
            return await self.murf_service.generate_premium_voice(
                response_text,
                voice_profile,
                {"urgency": strategy.get("urgency", "medium")}
            )
            
        except Exception as e:
            self.logger.error(f"Voice response generation error: {e}")
            return None
    
    async def _find_property_matches(self, session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find matching properties based on qualification data"""
        qual_data = session["qualification_data"]
        
        # This would integrate with actual property database
        # For demo, return sample matches
        sample_properties = [
            {
                "id": "PROP_BLR_001",
                "name": "Prestige Sunrise Park",
                "location": "Electronic City, Bangalore",
                "type": "3 BHK Apartment",
                "price": "₹85 Lakhs",
                "size": "1650 sqft",
                "possession": "Ready to Move",
                "match_score": 9.2,
                "match_reasons": ["Perfect budget fit", "Preferred location", "Ready possession"],
                "amenities": ["Swimming Pool", "Gym", "Children's Play Area", "24x7 Security"]
            },
            {
                "id": "PROP_BLR_002",
                "name": "Godrej Nature Plus",
                "location": "Sector 33, Gurgaon",
                "type": "2 BHK Apartment",
                "price": "₹75 Lakhs",
                "size": "1200 sqft",
                "possession": "Dec 2025",
                "match_score": 8.7,
                "match_reasons": ["Good investment potential", "Growing area", "Reputed builder"],
                "amenities": ["Club House", "Swimming Pool", "Landscaped Gardens", "Power Backup"]
            }
        ]
        
        # Filter based on qualification data
        filtered_properties = []
        for prop in sample_properties:
            if self._property_matches_criteria(prop, qual_data):
                filtered_properties.append(prop)
        
        session["property_matches"] = filtered_properties
        return filtered_properties
    
    def _property_matches_criteria(self, property_info: Dict[str, Any], qual_data: Dict[str, Any]) -> bool:
        """Check if property matches lead criteria"""
        # Simple matching logic - in production this would be more sophisticated
        
        # Budget matching
        budget_range = qual_data.get("budget_range", "")
        if budget_range and "not_disclosed" not in budget_range.lower():
            # Extract price from property and compare (simplified)
            pass  # Implementation would check price ranges
        
        # Location matching
        preferred_locations = qual_data.get("locations", [])
        if preferred_locations:
            property_location = property_info.get("location", "").lower()
            if not any(loc.lower() in property_location for loc in preferred_locations):
                # Might not match, but don't exclude completely
                pass
        
        # For demo, return True for most properties
        return True
    
    async def _update_session_state(self, session: Dict[str, Any], analysis: Dict[str, Any], strategy: Dict[str, Any]):
        """Update session state based on analysis and strategy"""
        
        # Update next best action
        session["next_best_action"] = strategy.get("response_type", "continue_qualification")
        
        # Add AI insights
        if analysis.get("agent_coaching"):
            coaching = analysis["agent_coaching"]
            insight = f"Conversation effectiveness: {coaching.get('conversation_effectiveness', 'good')}"
            session["ai_insights"].append({
                "timestamp": datetime.now().isoformat(),
                "insight": insight,
                "type": "coaching"
            })
        
        # Track response strategy
        session["conversation_history"].append({
            "timestamp": datetime.now().isoformat(),
            "speaker": "system",
            "text": f"AI Strategy: {strategy['response_type']}",
            "confidence": 1.0
        })
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive session summary"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        duration = (datetime.now() - session["start_time"]).total_seconds()
        
        return {
            "session_id": session_id,
            "duration_minutes": round(duration / 60, 2),
            "qualification_score": session["qualification_score"],
            "completion_percentage": session["completion_percentage"],
            "qualification_data": session["qualification_data"],
            "engagement_metrics": session["engagement_metrics"],
            "property_matches_found": len(session["property_matches"]),
            "next_recommended_action": session["next_best_action"],
            "ai_insights": session["ai_insights"][-5:],  # Last 5 insights
            "language_used": session["language_preference"],
            "session_quality": "high" if session["qualification_score"] >= 7 else "medium" if session["qualification_score"] >= 4 else "needs_improvement"
        }
    
    async def finalize_session(self, session_id: str):
        """Finalize and cleanup session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Generate final summary
            summary = await self.get_session_summary(session_id)
            
            # Cleanup
            del self.active_sessions[session_id]
            
            self.logger.info(f"Real estate session finalized: {session_id}")
            return summary
        
        return {"error": "Session not found"}
