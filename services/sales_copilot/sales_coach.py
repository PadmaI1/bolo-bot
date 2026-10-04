import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from ..azure_core.llm_service import MultiIndustryLLMRouter
from ..azure_core.murf_tts import EnhancedMurfTTSService

class RealTimeSalesCoach:
    def __init__(self, llm_service: MultiIndustryLLMRouter, tts_service: EnhancedMurfTTSService):
        self.llm_service = llm_service
        self.tts_service = tts_service
        self.logger = logging.getLogger(__name__)
        
        # Active coaching sessions
        self.active_sessions = {}
        
        # Sales coaching templates and knowledge base
        self.coaching_knowledge = {
            "discovery_frameworks": {
                "BANT": ["Budget", "Authority", "Need", "Timeline"],
                "MEDDIC": ["Metrics", "Economic Buyer", "Decision Criteria", "Decision Process", "Identify Pain", "Champion"],
                "SPIN": ["Situation", "Problem", "Implication", "Need-payoff"]
            },
            "objection_categories": {
                "price": ["budget", "cost", "expensive", "price", "roi", "investment"],
                "timing": ["time", "rush", "later", "think about", "discuss", "delay"],
                "authority": ["decision", "boss", "team", "approve", "management"],
                "need": ["don't need", "working fine", "satisfied", "current solution"],
                "trust": ["references", "proof", "case study", "guarantee", "risk"]
            },
            "buying_signals": [
                "when can we start", "what's the next step", "how long does implementation take",
                "can you send a proposal", "what are the payment terms", "references from similar companies",
                "who would be our account manager", "what does the contract look like"
            ]
        }
    
    def start_coaching_session(self, session_id: str, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a new sales coaching session"""
        self.active_sessions[session_id] = {
            "start_time": datetime.now(),
            "context": session_context,
            "conversation_history": [],
            "coaching_log": [],
            "metrics": {
                "rep_talk_time": 0,
                "customer_talk_time": 0,
                "questions_asked": 0,
                "objections_handled": 0,
                "buying_signals_detected": 0
            },
            "current_stage": "discovery",
            "risk_factors": [],
            "opportunities": []
        }
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Sales coaching session started",
            "initial_coaching": "Start with rapport building and discovery questions"
        }
    
    async def analyze_conversation_real_time(self, session_id: str, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """Real-time conversation analysis with immediate coaching"""
        try:
            if session_id not in self.active_sessions:
                return {"error": "Session not found"}
            
            session = self.active_sessions[session_id]
            transcript_text = transcript_data.get("text", "")
            speaker_type = transcript_data.get("speaker_type", "unknown")
            
            # Add to conversation history
            conversation_entry = {
                "timestamp": datetime.now().isoformat(),
                "speaker": speaker_type,
                "text": transcript_text,
                "duration": transcript_data.get("duration", 0)
            }
            session["conversation_history"].append(conversation_entry)
            
            # Update metrics
            self._update_session_metrics(session, conversation_entry)
            
            # Get recent conversation context (last 5 exchanges)
            recent_context = " ".join([
                f"{entry['speaker']}: {entry['text']}" 
                for entry in session["conversation_history"][-10:]
            ])
            
            # Analyze with LLM
            analysis = self.llm_service.route_and_analyze(
                transcript_text, 
                "sales", 
                {
                    "session_context": session["context"],
                    "conversation_stage": session["current_stage"],
                    "recent_conversation": recent_context,
                    "session_metrics": session["metrics"]
                }
            )
            
            # Generate coaching insights
            coaching_response = await self._generate_coaching_response(analysis, session)
            
            # Update session state
            self._update_session_state(session, analysis)
            
            # Log coaching interaction
            session["coaching_log"].append({
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis,
                "coaching_provided": coaching_response
            })
            
            return {
                "session_id": session_id,
                "analysis": analysis,
                "coaching": coaching_response,
                "session_metrics": session["metrics"],
                "conversation_stage": session["current_stage"]
            }
        
        except Exception as e:
            self.logger.error(f"Real-time analysis error: {e}")
            return {"error": str(e)}
    
    async def _generate_coaching_response(self, analysis: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive coaching response"""
        coaching_response = {
            "immediate_suggestions": [],
            "discovery_questions": [],
            "value_propositions": [],
            "objection_responses": [],
            "battle_cards": [],
            "next_steps": [],
            "risk_alerts": [],
            "audio_coaching": None
        }
        
        # Immediate coaching based on conversation stage
        conversation_stage = analysis.get("conversation_stage", "discovery")
        
        if conversation_stage == "discovery":
            coaching_response["immediate_suggestions"].append(
                "Focus on uncovering pain points. Ask about their current process and challenges."
            )
            coaching_response["discovery_questions"] = analysis.get("coaching_insights", {}).get("discovery_questions", [])
        
        elif conversation_stage == "presentation":
            coaching_response["immediate_suggestions"].append(
                "Connect features to their specific pain points. Focus on ROI and business impact."
            )
            coaching_response["value_propositions"] = analysis.get("coaching_insights", {}).get("value_props_to_mention", [])
        
        elif conversation_stage == "objection_handling":
            objection_info = analysis.get("objection_handling", {})
            if objection_info.get("objection_detected") != "none":
                coaching_response["objection_responses"].append({
                    "objection_type": objection_info.get("objection_detected"),
                    "severity": objection_info.get("objection_severity"),
                    "response_script": objection_info.get("recommended_response"),
                    "follow_up_questions": objection_info.get("follow_up_questions", [])
                })
                
                # Generate audio coaching for objection handling
                audio_coaching = self.tts_service.create_coaching_prompt(
                    objection_info.get("recommended_response", "Address the objection with empathy"),
                    urgency="high"
                )
                coaching_response["audio_coaching"] = audio_coaching
        
        # Competitor intelligence
        competitor_intel = analysis.get("competitor_intelligence", {})
        if competitor_intel.get("competitor_mentioned"):
            coaching_response["battle_cards"].append({
                "competitor": competitor_intel.get("competitor_mentioned"),
                "positioning_points": competitor_intel.get("battle_card_points", []),
                "strategy": competitor_intel.get("positioning_strategy")
            })
        
        # Risk assessment
        risks = analysis.get("coaching_insights", {}).get("risks_detected", [])
        for risk in risks:
            coaching_response["risk_alerts"].append({
                "risk_type": risk,
                "mitigation_strategy": self._get_risk_mitigation_strategy(risk),
                "urgency": "medium"
            })
        
        # Next best actions
        next_action = analysis.get("deal_progression", {}).get("next_best_action")
        if next_action:
            coaching_response["next_steps"].append({
                "action": next_action,
                "timeline": analysis.get("deal_progression", {}).get("timeline_urgency", "medium"),
                "success_criteria": self._get_success_criteria(next_action)
            })
        
        return coaching_response
    
    def _update_session_metrics(self, session: Dict[str, Any], conversation_entry: Dict[str, Any]):
        """Update session performance metrics"""
        speaker = conversation_entry["speaker"]
        duration = conversation_entry.get("duration", 0)
        text = conversation_entry["text"].lower()
        
        # Update talk time ratios
        if speaker == "agent":
            session["metrics"]["rep_talk_time"] += duration
        elif speaker == "customer":
            session["metrics"]["customer_talk_time"] += duration
        
        # Count questions asked by rep
        if speaker == "agent" and any(q in text for q in ["what", "how", "why", "when", "where", "can you", "do you"]):
            session["metrics"]["questions_asked"] += 1
        
        # Detect buying signals
        for signal in self.coaching_knowledge["buying_signals"]:
            if signal in text:
                session["metrics"]["buying_signals_detected"] += 1
                break
        
        # Count objections (from customer)
        if speaker == "customer":
            for objection_type, keywords in self.coaching_knowledge["objection_categories"].items():
                if any(keyword in text for keyword in keywords):
                    session["metrics"]["objections_handled"] += 1
                    break
    
    def _update_session_state(self, session: Dict[str, Any], analysis: Dict[str, Any]):
        """Update session state based on analysis"""
        # Update conversation stage
        new_stage = analysis.get("conversation_stage")
        if new_stage and new_stage != session["current_stage"]:
            session["current_stage"] = new_stage
        
        # Track opportunities
        buying_signals = analysis.get("sentiment_analysis", {}).get("buying_signals", [])
        session["opportunities"].extend(buying_signals)
        
        # Track risk factors
        risks = analysis.get("coaching_insights", {}).get("risks_detected", [])
        session["risk_factors"].extend(risks)
    
    def _get_risk_mitigation_strategy(self, risk_type: str) -> str:
        """Get mitigation strategy for specific risks"""
        strategies = {
            "price_sensitivity": "Focus on ROI and value, offer flexible payment terms",
            "multiple_stakeholders": "Identify all decision makers and their priorities",
            "competition_mentioned": "Use battle cards and differentiation strategy",
            "timeline_mismatch": "Understand urgency drivers and create compelling events",
            "feature_gaps": "Position around core business value and roadmap items"
        }
        return strategies.get(risk_type, "Monitor closely and address proactively")
    
    def _get_success_criteria(self, action_type: str) -> str:
        """Define success criteria for next actions"""
        criteria = {
            "schedule_demo": "Demo scheduled within 48 hours with key stakeholders",
            "send_proposal": "Proposal sent within 24 hours with clear next steps",
            "technical_call": "Technical validation call scheduled with IT team",
            "reference_call": "Customer reference call arranged with similar client",
            "executive_meeting": "C-level meeting scheduled to discuss strategic fit"
        }
        return criteria.get(action_type, "Action completed with clear follow-up defined")
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive session summary"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        duration = (datetime.now() - session["start_time"]).total_seconds()
        
        # Calculate performance metrics
        total_talk_time = session["metrics"]["rep_talk_time"] + session["metrics"]["customer_talk_time"]
        rep_talk_ratio = (session["metrics"]["rep_talk_time"] / total_talk_time * 100) if total_talk_time > 0 else 0
        
        summary = {
            "session_id": session_id,
            "duration_minutes": round(duration / 60, 2),
            "conversation_stage": session["current_stage"],
            "performance_metrics": {
                "rep_talk_ratio": round(rep_talk_ratio, 1),
                "questions_asked": session["metrics"]["questions_asked"],
                "objections_handled": session["metrics"]["objections_handled"],
                "buying_signals": session["metrics"]["buying_signals_detected"]
            },
            "key_insights": {
                "opportunities_identified": session["opportunities"],
                "risk_factors": session["risk_factors"],
                "coaching_interventions": len(session["coaching_log"])
            },
            "recommended_follow_up": self._generate_follow_up_recommendations(session),
            "crm_update_data": self._prepare_crm_data(session)
        }
        
        return summary
    
    def _generate_follow_up_recommendations(self, session: Dict[str, Any]) -> List[str]:
        """Generate follow-up recommendations based on session"""
        recommendations = []
        
        # Based on conversation stage
        if session["current_stage"] == "discovery":
            recommendations.append("Schedule technical deep-dive to understand requirements better")
        elif session["current_stage"] == "presentation":
            recommendations.append("Send detailed proposal with ROI calculations")
        elif session["current_stage"] == "objection_handling":
            recommendations.append("Provide additional proof points and customer references")
        
        # Based on buying signals
        if session["metrics"]["buying_signals_detected"] > 2:
            recommendations.append("Fast-track to contract discussion and implementation timeline")
        
        # Based on risks
        if "competition_mentioned" in session["risk_factors"]:
            recommendations.append("Schedule competitive positioning call with stakeholders")
        
        return recommendations
    
    def _prepare_crm_data(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare structured data for CRM sync"""
        return {
            "call_date": session["start_time"].isoformat(),
            "call_duration": (datetime.now() - session["start_time"]).total_seconds(),
            "conversation_stage": session["current_stage"],
            "key_discussion_points": [entry["text"] for entry in session["conversation_history"][-5:]],
            "next_steps": [log.get("coaching_provided", {}).get("next_steps", []) for log in session["coaching_log"]],
            "risk_assessment": session["risk_factors"],
            "opportunity_score": min(session["metrics"]["buying_signals_detected"] * 2, 10),
            "coaching_summary": f"Provided {len(session['coaching_log'])} coaching interventions during call"
        }
    
    def end_coaching_session(self, session_id: str) -> Dict[str, Any]:
        """End coaching session and cleanup"""
        if session_id in self.active_sessions:
            summary = self.get_session_summary(session_id)
            del self.active_sessions[session_id]
            return {
                "status": "success",
                "message": "Coaching session ended",
                "final_summary": summary
            }
        return {"error": "Session not found"}
