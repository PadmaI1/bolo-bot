import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from ..azure_core.llm_service import MultiIndustryLLMRouter
from ..azure_core.murf_tts.py import EnhancedMurfTTSService

class RealEstateLeadQualifier:
    def __init__(self, llm_service: MultiIndustryLLMRouter, tts_service: EnhancedMurfTTSService):
        self.llm_service = llm_service
        self.tts_service = tts_service
        self.logger = logging.getLogger(__name__)
        
        # Active lead qualification sessions
        self.active_sessions = {}
        
        # Lead qualification framework
        self.qualification_criteria = {
            "budget_ranges": {
                "entry_level": {"min": 20, "max": 50, "segment": "First-time buyers"},
                "mid_range": {"min": 50, "max": 150, "segment": "Upgraders/Investors"},
                "premium": {"min": 150, "max": 500, "segment": "HNI buyers"},
                "luxury": {"min": 500, "max": 2000, "segment": "Ultra HNI"}
            },
            "property_types": {
                "residential": ["1bhk", "2bhk", "3bhk", "4bhk", "villa", "penthouse"],
                "commercial": ["office", "retail", "warehouse", "co-working"],
                "land": ["residential_plot", "commercial_plot", "farmland", "industrial"]
            },
            "buying_motivations": {
                "self_use": {"priority": "location, amenities, lifestyle", "timeline": "immediate"},
                "investment": {"priority": "rental_yield, appreciation, liquidity", "timeline": "flexible"},
                "upgrade": {"priority": "space, location, amenities", "timeline": "medium"}
            },
            "qualification_questions": {
                "budget_discovery": [
                    "What budget range are you considering for this property?",
                    "Have you been pre-approved for a home loan?",
                    "Are you looking at cash purchase or would you need financing?",
                    "What EMI range would be comfortable for your family?"
                ],
                "requirement_gathering": [
                    "Is this property for your own use or investment?",
                    "Which areas are you considering, and why?",
                    "What size property are you looking for?",
                    "What amenities are must-haves for you?",
                    "When are you planning to make this purchase?"
                ],
                "family_dynamics": [
                    "Who else is involved in this property decision?",
                    "What are your family's key priorities for this property?",
                    "Do you have any specific requirements from family members?"
                ]
            }
        }
    
    def start_qualification_session(self, session_id: str, lead_info: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize lead qualification session"""
        self.active_sessions[session_id] = {
            "lead_info": lead_info,
            "start_time": datetime.now(),
            "conversation_log": [],
            "qualification_data": {
                "budget_range": None,
                "property_type": None,
                "locations": [],
                "timeline": None,
                "motivation": None,
                "financing_status": None,
                "family_involvement": None,
                "key_requirements": [],
                "objections": [],
                "hot_buttons": []
            },
            "qualification_score": 0,
            "engagement_level": "initial",
            "next_recommended_action": "start_qualification",
            "follow_up_strategy": None
        }
        
        # Generate personalized welcome message
        welcome_audio = self.tts_service.create_welcome_message(
            "real_estate", 
            lead_info.get("name", "Customer"),
            lead_info.get("preferred_language", "english")
        )
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Lead qualification session started",
            "welcome_audio": welcome_audio,
            "first_question": self._get_opening_question(lead_info)
        }
    
    async def process_lead_response(self, session_id: str, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process lead responses and continue qualification"""
        try:
            if session_id not in self.active_sessions:
                return {"error": "Session not found"}
            
            session = self.active_sessions[session_id]
            transcript_text = transcript_data.get("text", "")
            
            # Add to conversation log
            conversation_entry = {
                "timestamp": datetime.now().isoformat(),
                "speaker": transcript_data.get("speaker_type", "customer"),
                "text": transcript_text,
                "analysis_notes": ""
            }
            session["conversation_log"].append(conversation_entry)
            
            # Analyze response with industry-specific LLM
            recent_conversation = " ".join([
                f"{entry['speaker']}: {entry['text']}" 
                for entry in session["conversation_log"][-6:]
            ])
            
            analysis = self.llm_service.route_and_analyze(
                transcript_text,
                "real_estate",
                {
                    "lead_info": session["lead_info"],
                    "qualification_progress": session["qualification_data"],
                    "conversation_history": recent_conversation,
                    "session_stage": self._determine_qualification_stage(session)
                }
            )
            
            # Update qualification data based on analysis
            self._update_qualification_data(session, analysis)
            
            # Generate next question or response
            next_response = await self._generate_next_response(session, analysis)
            
            # Update session metrics
            self._update_session_metrics(session, analysis)
            
            return {
                "session_id": session_id,
                "analysis": analysis,
                "qualification_update": session["qualification_data"],
                "next_response": next_response,
                "session_progress": self._calculate_progress(session),
                "recommendation": self._get_current_recommendation(session)
            }
        
        except Exception as e:
            self.logger.error(f"Lead response processing error: {e}")
            return {"error": str(e)}
    
    def _get_opening_question(self, lead_info: Dict[str, Any]) -> str:
        """Generate contextual opening question"""
        source = lead_info.get("source", "website")
        interest = lead_info.get("interest_type", "general")
        
        if source == "website_form":
            return "I see you filled out our form showing interest in properties. Are you looking to buy for your own family or as an investment opportunity?"
        elif interest == "specific_property":
            property_name = lead_info.get("property_name", "our property")
            return f"Thank you for your interest in {property_name}. What specifically attracted you to this property?"
        else:
            return "I'd love to help you find the perfect property. Are you looking for a home for your family or an investment opportunity?"
    
    def _update_qualification_data(self, session: Dict[str, Any], analysis: Dict[str, Any]):
        """Update qualification data based on conversation analysis"""
        qual_data = session["qualification_data"]
        customer_profile = analysis.get("customer_profile", {})
        property_reqs = analysis.get("property_requirements", {})
        
        # Update budget information
        budget_range = customer_profile.get("budget_range")
        if budget_range and budget_range != "not_disclosed":
            qual_data["budget_range"] = budget_range
        
        # Update property preferences
        if property_reqs.get("property_type") != "any":
            qual_data["property_type"] = property_reqs.get("property_type")
        
        # Update location preferences
        locations = property_reqs.get("location_preferences", [])
        if locations and locations != ["any"]:
            qual_data["locations"].extend(locations)
            qual_data["locations"] = list(set(qual_data["locations"]))  # Remove duplicates
        
        # Update timeline
        timeline = customer_profile.get("decision_timeline")
        if timeline:
            qual_data["timeline"] = timeline
        
        # Update buyer type/motivation
        buyer_type = customer_profile.get("buyer_type")
        if buyer_type:
            qual_data["motivation"] = buyer_type
        
        # Update financing status
        financing = customer_profile.get("financing_status")
        if financing:
            qual_data["financing_status"] = financing
        
        # Extract key requirements
        insights = analysis.get("conversation_insights", {})
        requirements = insights.get("pain_points", []) + insights.get("motivation_factors", [])
        qual_data["key_requirements"].extend(requirements)
        
        # Track objections
        objections = insights.get("objections_concerns", [])
        qual_data["objections"].extend(objections)
        
        # Update qualification score
        session["qualification_score"] = self._calculate_qualification_score(qual_data, analysis)
    
    async def _generate_next_response(self, session: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the next appropriate response or question"""
        
        # Determine what information is still needed
        missing_info = self._identify_missing_qualification_info(session["qualification_data"])
        
        # Get suggested action from analysis
        next_action = analysis.get("next_actions", {})
        immediate_action = next_action.get("immediate_action", "continue_qualification")
        
        response_data = {
            "response_type": immediate_action,
            "text_response": "",
            "audio_response": None,
            "follow_up_timeline": next_action.get("follow_up_timeline", "same_day"),
            "confidence": analysis.get("lead_qualification", {}).get("conversion_probability", "medium")
        }
        
        # Generate appropriate response based on action
        if immediate_action == "site_visit":
            response_text = await self._generate_site_visit_response(session, analysis)
            response_data["audio_response"] = self.tts_service.create_industry_response(
                response_text, "real_estate", language=session["lead_info"].get("preferred_language", "english")
            )
            
        elif immediate_action == "send_properties":
            response_text = await self._generate_property_sharing_response(session, analysis)
            response_data["audio_response"] = self.tts_service.create_industry_response(
                response_text, "real_estate"
            )
            
        elif immediate_action == "schedule_call":
            response_text = await self._generate_callback_response(session, analysis)
            response_data["audio_response"] = self.tts_service.create_industry_response(
                response_text, "real_estate"
            )
            
        elif missing_info:
            # Continue qualification with next question
            next_question = self._get_next_qualification_question(missing_info[0], session)
            response_text = next_question
            response_data["audio_response"] = self.tts_service.create_industry_response(
                response_text, "real_estate"
            )
            
        else:
            # All info gathered, provide summary and next steps
            response_text = await self._generate_qualification_summary(session)
            response_data["audio_response"] = self.tts_service.create_industry_response(
                response_text, "real_estate"
            )
        
        response_data["text_response"] = response_text
        return response_data
    
    def _identify_missing_qualification_info(self, qual_data: Dict[str, Any]) -> List[str]:
        """Identify what qualification information is still missing"""
        missing = []
        
        if not qual_data.get("budget_range"):
            missing.append("budget")
        if not qual_data.get("property_type"):
            missing.append("property_type")
        if not qual_data.get("locations"):
            missing.append("location")
        if not qual_data.get("timeline"):
            missing.append("timeline")
        if not qual_data.get("motivation"):
            missing.append("motivation")
        if not qual_data.get("financing_status"):
            missing.append("financing")
        
        return missing
    
    def _get_next_qualification_question(self, info_type: str, session: Dict[str, Any]) -> str:
        """Get the next appropriate qualification question"""
        questions = {
            "budget": "What budget range are you considering for this property? This will help me show you the most suitable options.",
            "property_type": "What type of property interests you - an apartment, independent villa, or commercial space?",
            "location": "Which areas are you considering, and what's important to you about the location?",
            "timeline": "When are you planning to make this property purchase?",
            "motivation": "Is this property for your family's use or are you considering it as an investment?",
            "financing": "Are you planning a cash purchase, or would you be taking a home loan?"
        }
        
        return questions.get(info_type, "Tell me more about your property requirements.")
    
    async def _generate_site_visit_response(self, session: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate site visit scheduling response"""
        lead_name = session["lead_info"].get("name", "")
        
        return f"""
        Based on your requirements, I think you'd really like to see this property in person.
        The location and amenities align perfectly with what you're looking for.
        
        Would you be available this weekend for a site visit? 
        I can arrange it at your convenient time, and our property consultant will give you a complete walkthrough.
        
        We can also arrange pick-up and drop facility if needed. What works better for you - Saturday or Sunday?
        """
    
    async def _generate_property_sharing_response(self, session: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate property details sharing response"""
        
        return f"""
        Perfect! Based on your budget and location preferences, I have some excellent properties that match your criteria.
        
        Let me send you the complete details including floor plans, pricing, payment schemes, and high-resolution photos.
        
        I'll also include the ROI analysis for the investment options and EMI calculations for different loan tenures.
        
        Can I have your WhatsApp number to send these details immediately?
        """
    
    async def _generate_callback_response(self, session: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate callback scheduling response"""
        
        return f"""
        I understand you'd like to discuss this in detail. That's a smart approach for such an important decision.
        
        Let me schedule a comprehensive consultation call where we can go through all your options,
        discuss market trends, and answer any questions you might have.
        
        I'm available tomorrow evening or this weekend. What time works best for you?
        I'll also prepare a customized property portfolio based on today's discussion.
        """
    
    async def _generate_qualification_summary(self, session: Dict[str, Any]) -> str:
        """Generate qualification completion summary"""
        qual_data = session["qualification_data"]
        lead_name = session["lead_info"].get("name", "")
        
        return f"""
        Thank you for sharing all the details, {lead_name}. 
        
        Based on our conversation, I understand you're looking for a {qual_data.get('property_type', 'property')} 
        in {', '.join(qual_data.get('locations', ['your preferred area'])[:2])} 
        with a budget of around {qual_data.get('budget_range', 'your specified range')}.
        
        I have some excellent options that match exactly what you're looking for. 
        My next step would be to send you a curated list of properties and arrange site visits for the most promising ones.
        
        Can I send the property details to your WhatsApp, and shall we schedule the first site visit for this weekend?
        """
    
    def _calculate_qualification_score(self, qual_data: Dict[str, Any], analysis: Dict[str, Any]) -> int:
        """Calculate lead qualification score (1-10)"""
        score = 0
        
        # Budget clarity (25% weight)
        if qual_data.get("budget_range") and qual_data["budget_range"] != "not_disclosed":
            score += 2.5
        
        # Timeline urgency (20% weight)
        timeline = qual_data.get("timeline", "")
        if timeline == "immediate":
            score += 2.0
        elif timeline == "1-3months":
            score += 1.5
        elif timeline == "3-6months":
            score += 1.0
        
        # Property type clarity (15% weight)
        if qual_data.get("property_type"):
            score += 1.5
        
        # Location preferences (15% weight)
        if qual_data.get("locations"):
            score += 1.5
        
        # Financing readiness (15% weight)
        financing = qual_data.get("financing_status", "")
        if financing in ["pre_approved", "cash_buyer"]:
            score += 1.5
        elif financing == "loan_required":
            score += 1.0
        
        # Engagement and buying signals (10% weight)
        conversion_prob = analysis.get("lead_qualification", {}).get("conversion_probability", "low")
        if conversion_prob == "high":
            score += 1.0
        elif conversion_prob == "medium":
            score += 0.5
        
        return min(int(score), 10)
    
    def _determine_qualification_stage(self, session: Dict[str, Any]) -> str:
        """Determine current qualification stage"""
        qual_data = session["qualification_data"]
        missing_info = self._identify_missing_qualification_info(qual_data)
        
        if len(missing_info) > 4:
            return "initial"
        elif len(missing_info) > 2:
            return "gathering_requirements"
        elif len(missing_info) > 0:
            return "finalizing_details"
        else:
            return "qualified"
    
    def _update_session_metrics(self, session: Dict[str, Any], analysis: Dict[str, Any]):
        """Update session engagement and progression metrics"""
        
        # Update engagement level
        engagement_indicators = analysis.get("conversation_insights", {})
        
        if engagement_indicators.get("pain_points") or engagement_indicators.get("motivation_factors"):
            session["engagement_level"] = "high"
        elif analysis.get("lead_qualification", {}).get("conversion_probability") == "medium":
            session["engagement_level"] = "medium"
        
        # Track qualification progress
        stage = self._determine_qualification_stage(session)
        session["current_qualification_stage"] = stage
    
    def _calculate_progress(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall qualification progress"""
        qual_data = session["qualification_data"]
        total_criteria = 6  # budget, type, location, timeline, motivation, financing
        
        completed_criteria = sum([
            1 if qual_data.get("budget_range") else 0,
            1 if qual_data.get("property_type") else 0,
            1 if qual_data.get("locations") else 0,
            1 if qual_data.get("timeline") else 0,
            1 if qual_data.get("motivation") else 0,
            1 if qual_data.get("financing_status") else 0
        ])
        
        progress_percentage = (completed_criteria / total_criteria) * 100
        
        return {
            "progress_percentage": round(progress_percentage),
            "completed_criteria": completed_criteria,
            "total_criteria": total_criteria,
            "current_stage": session.get("current_qualification_stage", "initial"),
            "qualification_score": session["qualification_score"],
            "ready_for_next_step": progress_percentage >= 80
        }
    
    def _get_current_recommendation(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Get current recommendation for the lead"""
        qual_score = session["qualification_score"]
        progress = self._calculate_progress(session)
        
        if qual_score >= 8 and progress["ready_for_next_step"]:
            recommendation = {
                "priority": "high",
                "action": "immediate_site_visit",
                "reasoning": "Highly qualified lead ready for next step",
                "timeline": "within_24_hours",
                "sales_approach": "consultative_close"
            }
        elif qual_score >= 6:
            recommendation = {
                "priority": "medium",
                "action": "send_properties_and_follow_up",
                "reasoning": "Good qualification, needs more information",
                "timeline": "within_48_hours",
                "sales_approach": "value_demonstration"
            }
        elif qual_score >= 4:
            recommendation = {
                "priority": "medium",
                "action": "nurture_campaign",
                "reasoning": "Potential lead, needs more qualification",
                "timeline": "within_week",
                "sales_approach": "education_and_trust_building"
            }
        else:
            recommendation = {
                "priority": "low",
                "action": "long_term_nurture",
                "reasoning": "Early stage lead, continue relationship building",
                "timeline": "monthly_touchpoint",
                "sales_approach": "market_education"
            }
        
        return recommendation
    
    def generate_lead_summary(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive lead qualification summary"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        duration = (datetime.now() - session["start_time"]).total_seconds() / 60
        
        summary = {
            "lead_info": session["lead_info"],
            "session_duration_minutes": round(duration, 2),
            "qualification_data": session["qualification_data"],
            "qualification_score": session["qualification_score"],
            "engagement_level": session["engagement_level"],
            "conversation_summary": self._create_conversation_summary(session),
            "recommended_properties": self._suggest_matching_properties(session),
            "next_actions": self._recommend_next_actions(session),
            "crm_data": self._prepare_crm_lead_data(session),
            "follow_up_strategy": self._create_follow_up_strategy(session)
        }
        
        return summary
    
    def _create_conversation_summary(self, session: Dict[str, Any]) -> str:
        """Create human-readable conversation summary"""
        qual_data = session["qualification_data"]
        lead_name = session["lead_info"].get("name", "Lead")
        
        summary_parts = [
            f"{lead_name} is looking for a {qual_data.get('property_type', 'property')}"
        ]
        
        if qual_data.get("budget_range"):
            summary_parts.append(f"with budget {qual_data['budget_range']}")
        
        if qual_data.get("locations"):
            summary_parts.append(f"in {', '.join(qual_data['locations'][:2])}")
        
        if qual_data.get("motivation"):
            summary_parts.append(f"for {qual_data['motivation']}")
        
        if qual_data.get("timeline"):
            summary_parts.append(f"with {qual_data['timeline']} timeline")
        
        base_summary = " ".join(summary_parts) + "."
        
        # Add key insights
        if qual_data.get("key_requirements"):
            base_summary += f" Key requirements: {', '.join(qual_data['key_requirements'][:3])}."
        
        if qual_data.get("objections"):
            base_summary += f" Concerns raised: {', '.join(qual_data['objections'][:2])}."
        
        return base_summary
    
    def _suggest_matching_properties(self, session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest properties that match lead qualification"""
        # This would integrate with actual property inventory
        qual_data = session["qualification_data"]
        
        # Sample property matching logic
        matching_properties = [
            {
                "property_id": "PROP001",
                "name": "Prestige Sunrise Park",
                "location": "Electronic City, Bangalore",
                "type": "3 BHK Apartment",
                "price": "₹85 Lakhs",
                "match_score": 9,
                "match_reasons": ["Budget fit", "Location preference", "Property type match"],
                "key_highlights": ["Ready possession", "Premium amenities", "Good connectivity"]
            },
            {
                "property_id": "PROP002",
                "name": "Godrej Nature Plus", 
                "location": "Sector 33, Gurgaon",
                "type": "2 BHK Apartment",
                "price": "₹1.2 Crores",
                "match_score": 7,
                "match_reasons": ["Investment potential", "Brand value"],
                "key_highlights": ["Under construction", "Good appreciation potential", "Modern amenities"]
            }
        ]
        
        # Filter based on qualification data
        budget_filter = qual_data.get("budget_range")
        type_filter = qual_data.get("property_type")
        location_filter = qual_data.get("locations", [])
        
        # Simple filtering logic (would be more sophisticated in production)
        filtered_properties = []
        for prop in matching_properties:
            if self._property_matches_criteria(prop, qual_data):
                filtered_properties.append(prop)
        
        return filtered_properties[:5]  # Return top 5 matches
    
    def _property_matches_criteria(self, property_info: Dict[str, Any], qual_data: Dict[str, Any]) -> bool:
        """Check if property matches lead qualification criteria"""
        # This would contain sophisticated matching logic
        # For now, simple demonstration
        return True
    
    def _recommend_next_actions(self, session: Dict[str, Any]) -> List[Dict[str, str]]:
        """Recommend specific next actions for this lead"""
        score = session["qualification_score"]
        qual_data = session["qualification_data"]
        
        actions = []
        
        if score >= 8:
            actions.extend([
                {
                    "action": "immediate_site_visit",
                    "description": "Schedule site visit within 24 hours",
                    "priority": "high",
                    "owner": "sales_team"
                },
                {
                    "action": "send_property_portfolio", 
                    "description": "Send curated property options",
                    "priority": "high",
                    "owner": "marketing_team"
                }
            ])
        elif score >= 6:
            actions.extend([
                {
                    "action": "detailed_follow_up_call",
                    "description": "Schedule detailed consultation within 48 hours", 
                    "priority": "medium",
                    "owner": "sales_team"
                },
                {
                    "action": "market_analysis_report",
                    "description": "Send location-specific market analysis",
                    "priority": "medium", 
                    "owner": "research_team"
                }
            ])
        else:
            actions.extend([
                {
                    "action": "nurture_sequence",
                    "description": "Add to automated nurture campaign",
                    "priority": "low",
                    "owner": "marketing_team"
                },
                {
                    "action": "market_education",
                    "description": "Send market education content",
                    "priority": "low",
                    "owner": "content_team"
                }
            ])
        
        return actions
    
    def _prepare_crm_lead_data(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare lead data for CRM sync"""
        qual_data = session["qualification_data"]
        lead_info = session["lead_info"]
        
        return {
            "lead_id": lead_info.get("id"),
            "name": lead_info.get("name"),
            "phone": lead_info.get("phone"),
            "email": lead_info.get("email"),
            "source": lead_info.get("source", "Voice AI Qualification"),
            "qualification_score": session["qualification_score"],
            "budget_range": qual_data.get("budget_range"),
            "property_type": qual_data.get("property_type"),
            "preferred_locations": qual_data.get("locations"),
            "timeline": qual_data.get("timeline"),
            "buyer_type": qual_data.get("motivation"),
            "financing_status": qual_data.get("financing_status"),
            "key_requirements": qual_data.get("key_requirements"),
            "objections_concerns": qual_data.get("objections"),
            "conversation_summary": self._create_conversation_summary(session),
            "last_interaction": datetime.now().isoformat(),
            "next_follow_up": self._suggest_follow_up_date(session),
            "assigned_to": "sales_team",
            "lead_status": self._determine_lead_status(session["qualification_score"])
        }
    
    def _create_follow_up_strategy(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Create personalized follow-up strategy"""
        qual_score = session["qualification_score"]
        qual_data = session["qualification_data"]
        
        if qual_score >= 8:
            strategy = {
                "approach": "immediate_engagement",
                "timeline": "within_24_hours",
                "method": "personal_call_and_site_visit",
                "message_tone": "urgent_but_consultative",
                "key_focus": "closing_and_documentation"
            }
        elif qual_score >= 6:
            strategy = {
                "approach": "consultative_nurturing", 
                "timeline": "within_48_hours",
                "method": "detailed_presentation_call",
                "message_tone": "educational_and_helpful",
                "key_focus": "building_trust_and_demonstrating_value"
            }
        else:
            strategy = {
                "approach": "long_term_relationship",
                "timeline": "weekly_touchpoints",
                "method": "market_education_content",
                "message_tone": "helpful_and_informative",
                "key_focus": "market_education_and_awareness"
            }
        
        return strategy
    
    def _suggest_follow_up_date(self, session: Dict[str, Any]) -> str:
        """Suggest optimal follow-up date"""
        score = session["qualification_score"]
        timeline = session["qualification_data"].get("timeline", "exploring")
        
        if score >= 8 and timeline == "immediate":
            return (datetime.now() + timedelta(hours=24)).isoformat()
        elif score >= 6:
            return (datetime.now() + timedelta(days=2)).isoformat()
        elif timeline in ["1-3months", "3-6months"]:
            return (datetime.now() + timedelta(weeks=1)).isoformat()
        else:
            return (datetime.now() + timedelta(weeks=4)).isoformat()
    
    def _determine_lead_status(self, score: int) -> str:
        """Determine CRM lead status based on qualification score"""
        if score >= 8:
            return "hot_lead"
        elif score >= 6:
            return "warm_lead"
        elif score >= 4:
            return "qualified_lead"
        else:
            return "raw_lead"
    
    def end_qualification_session(self, session_id: str) -> Dict[str, Any]:
        """End qualification session and return final summary"""
        if session_id in self.active_sessions:
            summary = self.generate_lead_summary(session_id)
            del self.active_sessions[session_id]
            return {
                "status": "success",
                "message": "Lead qualification completed",
                "final_summary": summary
            }
        return {"error": "Session not found"}
