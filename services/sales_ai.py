import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time

class SalesAIEngine:
    """Advanced AI engine for sales copilot functionality"""
    
    def __init__(self, azure_service, murf_service, websocket_manager):
        self.azure_service = azure_service
        self.murf_service = murf_service
        self.websocket_manager = websocket_manager
        self.logger = logging.getLogger(__name__)
        
        # Active sales sessions
        self.active_sessions = {}
        
        # Sales coaching knowledge base
        self.coaching_frameworks = {
            "BANT": {
                "Budget": ["What budget have you allocated?", "What's your investment range?"],
                "Authority": ["Who makes the final decision?", "Who else is involved?"],
                "Need": ["What's your biggest challenge?", "What's driving this need?"],
                "Timeline": ["When do you need this implemented?", "What's your timeline?"]
            },
            "MEDDIC": {
                "Metrics": ["What metrics define success?", "How do you measure ROI?"],
                "Economic_Buyer": ["Who controls the budget?", "Who signs off financially?"],
                "Decision_Criteria": ["What factors are most important?", "How will you choose?"],
                "Decision_Process": ["What's your evaluation process?", "What are the steps?"],
                "Identify_Pain": ["What's the impact of doing nothing?", "What's broken today?"],
                "Champion": ["Who internally supports this?", "Who's driving this initiative?"]
            },
            "SPIN": {
                "Situation": ["Tell me about your current setup", "How do you handle this today?"],
                "Problem": ["What challenges does that create?", "Where does that hurt most?"],
                "Implication": ["What happens if you don't fix this?", "How does that impact growth?"],
                "Need_Payoff": ["How would solving this help?", "What value would that create?"]
            }
        }
        
        # Real-time coaching patterns
        self.coaching_triggers = {
            "customer_objection": {
                "patterns": ["too expensive", "not sure", "think about it", "budget", "timing"],
                "responses": "objection_handling"
            },
            "buying_signals": {
                "patterns": ["when can we start", "how long", "next steps", "proposal", "contract"],
                "responses": "accelerate_close"
            },
            "competitor_mention": {
                "patterns": ["salesforce", "hubspot", "zoho", "competitor", "other solution"],
                "responses": "battle_card"
            },
            "technical_questions": {
                "patterns": ["how does it work", "integration", "api", "security", "compliance"],
                "responses": "technical_validation"
            }
        }
    
    async def initialize_sales_session(self, session_id: str, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a new sales coaching session"""
        try:
            self.active_sessions[session_id] = {
                "session_id": session_id,
                "start_time": datetime.now(),
                "context": session_context,
                "conversation_history": [],
                "coaching_log": [],
                "current_framework": "BANT",  # Default framework
                "qualification_status": {
                    "Budget": "unknown",
                    "Authority": "unknown", 
                    "Need": "unknown",
                    "Timeline": "unknown"
                },
                "deal_stage": "discovery",
                "coaching_metrics": {
                    "questions_asked": 0,
                    "objections_raised": 0,
                    "buying_signals": 0,
                    "talk_time_ratio": 0.0,
                    "engagement_score": 5.0
                },
                "next_best_actions": [],
                "risk_factors": [],
                "opportunities": []
            }
            
            # Send initial coaching prompt
            initial_coaching = await self._generate_initial_coaching(session_context)
            
            return {
                "status": "success",
                "session_id": session_id,
                "initial_coaching": initial_coaching,
                "coaching_framework": "BANT",
                "message": "Sales coaching session initialized"
            }
            
        except Exception as e:
            self.logger.error(f"Sales session initialization error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def process_sales_conversation(self, session_id: str, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sales conversation and provide real-time coaching"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        try:
            session = self.active_sessions[session_id]
            transcript_text = transcript_data.get("text", "")
            speaker = transcript_data.get("speaker_detected", "unknown")
            
            # Add to conversation history
            conversation_entry = {
                "timestamp": datetime.now().isoformat(),
                "speaker": speaker,
                "text": transcript_text,
                "confidence": transcript_data.get("confidence", 0.8)
            }
            session["conversation_history"].append(conversation_entry)
            
            # Update metrics based on speaker
            await self._update_conversation_metrics(session, conversation_entry)
            
            # Get recent conversation context
            recent_context = self._build_conversation_context(session)
            
            # Analyze with Azure AI
            analysis_result = await self.azure_service.analyze_conversation_advanced(
                transcript_text,
                "sales", 
                {
                    "session_context": session["context"],
                    "conversation_history": recent_context,
                    "current_framework": session["current_framework"],
                    "deal_stage": session["deal_stage"],
                    "qualification_status": session["qualification_status"]
                }
            )
            
            # Generate coaching response
            coaching_response = await self._process_analysis_for_coaching(session, analysis_result)
            
            # Check for immediate triggers
            trigger_response = await self._check_coaching_triggers(session, transcript_text, speaker)
            if trigger_response:
                coaching_response["immediate_trigger"] = trigger_response
            
            # Update session state
            await self._update_session_state(session, analysis_result, coaching_response)
            
            # Generate voice coaching if needed
            if coaching_response.get("voice_coaching_needed"):
                voice_response = await self._generate_voice_coaching(session, coaching_response)
                coaching_response["voice_audio"] = voice_response
            
            return {
                "session_id": session_id,
                "analysis": analysis_result,
                "coaching": coaching_response,
                "session_metrics": session["coaching_metrics"],
                "deal_progression": {
                    "stage": session["deal_stage"],
                    "qualification_status": session["qualification_status"],
                    "next_actions": session["next_best_actions"]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Sales conversation processing error: {e}")
            return {"error": str(e)}
    
    async def _generate_initial_coaching(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate initial coaching guidance"""
        meeting_type = context.get("meeting_type", "discovery")
        
        initial_prompts = {
            "discovery": {
                "main_objective": "Uncover customer needs and pain points",
                "key_questions": self.coaching_frameworks["BANT"]["Need"],
                "success_metrics": "Customer shares specific challenges and timeline"
            },
            "demo": {
                "main_objective": "Connect features to specific customer needs",
                "key_questions": ["How would this solve your specific challenge?", "What impact would this have?"],
                "success_metrics": "Customer expresses interest in specific features"
            },
            "proposal": {
                "main_objective": "Address concerns and secure commitment",
                "key_questions": ["What questions do you have?", "What would make this a yes?"],
                "success_metrics": "Customer commits to next steps or timeline"
            }
        }
        
        return initial_prompts.get(meeting_type, initial_prompts["discovery"])
    
    async def _update_conversation_metrics(self, session: Dict[str, Any], conversation_entry: Dict[str, Any]):
        """Update real-time conversation metrics"""
        speaker = conversation_entry["speaker"]
        text = conversation_entry["text"]
        
        # Update talk time ratio
        if speaker == "agent":
            session["coaching_metrics"]["questions_asked"] += len([q for q in ["what", "how", "why", "when", "where"] if q in text.lower()])
        
        # Track engagement indicators
        text_lower = text.lower()
        
        # Detect objections
        objection_indicators = ["expensive", "budget", "not sure", "think about", "concern", "worried"]
        if any(indicator in text_lower for indicator in objection_indicators):
            session["coaching_metrics"]["objections_raised"] += 1
        
        # Detect buying signals
        buying_indicators = ["when can", "how long", "next step", "proposal", "start", "implement"]
        if any(indicator in text_lower for indicator in buying_indicators):
            session["coaching_metrics"]["buying_signals"] += 1
        
        # Calculate engagement score based on conversation flow
        session["coaching_metrics"]["engagement_score"] = min(10.0, 
            5.0 + session["coaching_metrics"]["buying_signals"] - session["coaching_metrics"]["objections_raised"] * 0.5
        )
    
    def _build_conversation_context(self, session: Dict[str, Any]) -> str:
        """Build conversation context for analysis"""
        recent_messages = session["conversation_history"][-10:]  # Last 10 messages
        context_parts = []
        
        for msg in recent_messages:
            speaker_label = "Rep" if msg["speaker"] == "agent" else "Customer"
            context_parts.append(f"{speaker_label}: {msg['text']}")
        
        return "\n".join(context_parts)
    
    async def _process_analysis_for_coaching(self, session: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Process AI analysis and generate specific coaching"""
        coaching_response = {
            "coaching_type": "real_time",
            "priority": "medium",
            "coaching_insights": [],
            "action_items": [],
            "voice_coaching_needed": False,
            "framework_guidance": {}
        }
        
        # Process different types of insights
        if "coaching_insights" in analysis:
            insights = analysis["coaching_insights"]
            
            # Immediate action coaching
            if insights.get("immediate_action"):
                coaching_response["coaching_insights"].append({
                    "type": "immediate_action",
                    "message": insights["immediate_action"],
                    "priority": "high"
                })
                coaching_response["voice_coaching_needed"] = True
            
            # Discovery question suggestions
            if insights.get("discovery_questions"):
                coaching_response["coaching_insights"].append({
                    "type": "discovery_questions", 
                    "questions": insights["discovery_questions"][:2],  # Top 2 questions
                    "priority": "medium"
                })
            
            # Risk alerts
            if insights.get("risk_alerts"):
                coaching_response["coaching_insights"].append({
                    "type": "risk_alert",
                    "risks": insights["risk_alerts"],
                    "priority": "high"
                })
                coaching_response["voice_coaching_needed"] = True
        
        # Handle objections
        if "objection_handling" in analysis:
            objection_info = analysis["objection_handling"]
            if objection_info.get("objection_type") != "none":
                coaching_response["coaching_insights"].append({
                    "type": "objection_response",
                    "objection_type": objection_info["objection_type"],
                    "recommended_response": objection_info["recommended_response"],
                    "priority": "high"
                })
                coaching_response["voice_coaching_needed"] = True
        
        # Framework-specific guidance
        current_framework = session["current_framework"]
        if current_framework in self.coaching_frameworks:
            framework_guidance = await self._generate_framework_guidance(session, analysis, current_framework)
            coaching_response["framework_guidance"] = framework_guidance
        
        return coaching_response
    
    async def _check_coaching_triggers(self, session: Dict[str, Any], transcript: str, speaker: str) -> Optional[Dict[str, Any]]:
        """Check for immediate coaching triggers"""
        text_lower = transcript.lower()
        
        for trigger_type, trigger_config in self.coaching_triggers.items():
            if any(pattern in text_lower for pattern in trigger_config["patterns"]):
                return {
                    "trigger_type": trigger_type,
                    "response_type": trigger_config["responses"],
                    "original_text": transcript,
                    "speaker": speaker,
                    "action_needed": True
                }
        
        return None
    
    async def _generate_framework_guidance(self, session: Dict[str, Any], analysis: Dict[str, Any], framework: str) -> Dict[str, Any]:
        """Generate guidance based on sales framework"""
        framework_data = self.coaching_frameworks[framework]
        qualification_status = session["qualification_status"]
        
        guidance = {
            "framework": framework,
            "completed_areas": [],
            "missing_areas": [],
            "suggested_questions": []
        }
        
        for area, status in qualification_status.items():
            if status == "unknown" and area in framework_data:
                guidance["missing_areas"].append(area)
                guidance["suggested_questions"].extend(framework_data[area][:1])  # One question per area
            else:
                guidance["completed_areas"].append(area)
        
        return guidance
    
    async def _generate_voice_coaching(self, session: Dict[str, Any], coaching_response: Dict[str, Any]) -> Optional[bytes]:
        """Generate voice coaching using Murf AI"""
        try:
            # Find the highest priority coaching insight
            high_priority_insights = [
                insight for insight in coaching_response["coaching_insights"] 
                if insight.get("priority") == "high"
            ]
            
            if not high_priority_insights:
                return None
            
            insight = high_priority_insights[0]
            coaching_text = ""
            
            if insight["type"] == "immediate_action":
                coaching_text = f"Coaching tip: {insight['message']}"
            elif insight["type"] == "objection_response":
                coaching_text = f"Handle this objection: {insight['recommended_response']}"
            elif insight["type"] == "risk_alert":
                coaching_text = f"Risk alert: {', '.join(insight['risks'][:2])}"
            
            if coaching_text:
                # Generate voice using premium sales coaching voice
                return await self.murf_service.generate_premium_voice(
                    coaching_text,
                    "sales_coach_male_confident"
                )
        
        except Exception as e:
            self.logger.error(f"Voice coaching generation error: {e}")
        
        return None
    
    async def _update_session_state(self, session: Dict[str, Any], analysis: Dict[str, Any], coaching: Dict[str, Any]):
        """Update session state based on analysis"""
        
        # Update deal progression
        if "deal_progression" in analysis:
            progression = analysis["deal_progression"]
            session["deal_stage"] = progression.get("next_best_action", session["deal_stage"])
            
            # Update next actions
            if progression.get("next_best_action"):
                session["next_best_actions"] = [progression["next_best_action"]]
        
        # Update qualification status from analysis
        if "crm_insights" in analysis:
            crm_insights = analysis["crm_insights"]
            # Extract qualification updates from conversation
            # This would be more sophisticated in production
        
        # Log coaching interaction
        session["coaching_log"].append({
            "timestamp": datetime.now().isoformat(),
            "analysis_summary": analysis.get("conversation_stage", "unknown"),
            "coaching_provided": len(coaching["coaching_insights"]),
            "voice_coaching": coaching["voice_coaching_needed"]
        })
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive session summary"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        duration = (datetime.now() - session["start_time"]).total_seconds()
        
        # Calculate performance metrics
        metrics = session["coaching_metrics"]
        total_messages = len(session["conversation_history"])
        agent_messages = len([msg for msg in session["conversation_history"] if msg["speaker"] == "agent"])
        
        return {
            "session_id": session_id,
            "duration_minutes": round(duration / 60, 2),
            "total_messages": total_messages,
            "agent_talk_ratio": round((agent_messages / max(total_messages, 1)) * 100, 1),
            "coaching_metrics": metrics,
            "qualification_status": session["qualification_status"],
            "deal_stage": session["deal_stage"],
            "coaching_interventions": len(session["coaching_log"]),
            "next_recommended_actions": session["next_best_actions"],
            "session_effectiveness": "high" if metrics["engagement_score"] > 7 else "medium" if metrics["engagement_score"] > 4 else "low"
        }
    
    async def finalize_session(self, session_id: str):
        """Finalize and cleanup session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Generate final summary
            summary = await self.get_session_summary(session_id)
            
            # Clean up resources
            del self.active_sessions[session_id]
            
            self.logger.info(f"Sales session finalized: {session_id}")
            return summary
        
        return {"error": "Session not found"}
