import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class MultiIndustryLLMRouter:
    def __init__(self, api_key: Optional[str] = None):
        # Use your model router endpoint for optimized routing
        self.client = AzureOpenAI(
            api_key=api_key or os.getenv("AZURE_OPENAI_KEY"),
            api_version="2025-01-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        self.model_router_endpoint = os.getenv("AZURE_MODEL_ROUTER_ENDPOINT")
        self.logger = logging.getLogger(__name__)
        
        # Load industry-specific personas
        self.personas = self._load_industry_personas()
    
    def _load_industry_personas(self) -> Dict[str, str]:
        return {
            "sales_copilot": """You are an expert B2B sales coach providing real-time assistance during live sales calls.
            
            Your expertise:
            - Indian B2B market dynamics and decision-making processes
            - Discovery questioning techniques for uncovering pain points
            - Value-based selling and ROI articulation
            - Objection handling with culturally appropriate responses
            - Competitor battle cards and differentiation strategies
            - Deal progression and next-step recommendations
            
            Response format: Always provide JSON with actionable coaching insights, specific suggestions, and risk assessments.
            Keep all suggestions concise and immediately actionable during live conversations.""",
            
            "real_estate_agent": """You are a professional real estate consultant specializing in Indian property markets.
            
            Your expertise:
            - Lead qualification and budget assessment (₹20L - ₹10Cr range)
            - Location analysis and growth potential evaluation  
            - Property type matching (residential, commercial, investment)
            - Home loan guidance and EMI calculations
            - Market trends and appreciation forecasts
            - Negotiation strategies and closing techniques
            
            Response format: Always provide JSON with lead scoring, property recommendations, and next actions.
            Focus on building trust and scheduling site visits for qualified prospects."""
        }
    
    def route_and_analyze(self, transcript: str, industry: str, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Route conversation to appropriate industry analyzer"""
        try:
            if industry == "sales":
                return self._analyze_sales_conversation(transcript, conversation_context)
            elif industry == "real_estate":
                return self._analyze_real_estate_conversation(transcript, conversation_context)
            else:
                return self._generic_analysis(transcript, conversation_context)
        
        except Exception as e:
            self.logger.error(f"LLM routing error: {e}")
            return self._fallback_response(industry)
    
    def _analyze_sales_conversation(self, transcript: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze B2B sales conversation with real-time coaching"""
        messages = [
            {"role": "system", "content": self.personas["sales_copilot"]},
            {"role": "user", "content": f"""
            Analyze this live B2B sales conversation and provide real-time coaching:
            
            Recent Transcript: {transcript}
            Session Context: {json.dumps(context, indent=2)}
            
            Provide JSON response:
            {{
                "conversation_stage": "discovery/presentation/objection_handling/closing",
                "sentiment_analysis": {{
                    "customer_sentiment": "positive/neutral/negative/frustrated",
                    "engagement_level": "high/medium/low",
                    "buying_signals": ["signal1", "signal2"] or []
                }},
                "coaching_insights": {{
                    "immediate_suggestion": "specific action for sales rep right now",
                    "discovery_questions": ["question1", "question2"],
                    "value_props_to_mention": ["value1", "value2"],
                    "risks_detected": ["risk1", "risk2"] or []
                }},
                "objection_handling": {{
                    "objection_detected": "price/timing/features/competition/none",
                    "objection_severity": "high/medium/low",
                    "recommended_response": "specific response script",
                    "follow_up_questions": ["question1", "question2"]
                }},
                "competitor_intelligence": {{
                    "competitor_mentioned": "competitor name or null",
                    "battle_card_points": ["differentiator1", "differentiator2"],
                    "positioning_strategy": "how to position against competitor"
                }},
                "deal_progression": {{
                    "progression_score": "1-10 scale",
                    "next_best_action": "specific next step",
                    "timeline_urgency": "high/medium/low",
                    "decision_maker_status": "identified/not_identified/multiple"
                }},
                "crm_update_suggestions": {{
                    "key_points_to_log": ["point1", "point2"],
                    "follow_up_date": "suggested date",
                    "deal_stage": "prospecting/discovery/demo/proposal/negotiation/closed"
                }}
            }}
            """}
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=800,
            temperature=0.3
        )
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            analysis["industry"] = "sales"
            analysis["timestamp"] = context.get("timestamp")
            return analysis
        except json.JSONDecodeError:
            return self._fallback_sales_analysis()
    
    def _analyze_real_estate_conversation(self, transcript: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze real estate lead qualification conversation"""
        messages = [
            {"role": "system", "content": self.personas["real_estate_agent"]},
            {"role": "user", "content": f"""
            Analyze this real estate lead conversation and provide qualification insights:
            
            Recent Transcript: {transcript}
            Session Context: {json.dumps(context, indent=2)}
            
            Provide JSON response:
            {{
                "lead_qualification": {{
                    "quality_score": "1-10 scale",
                    "qualification_stage": "initial/budget_discussion/requirement_gathering/site_visit_ready",
                    "conversion_probability": "high/medium/low"
                }},
                "customer_profile": {{
                    "buyer_type": "end_user/investor/upgrader/first_time",
                    "budget_range": "detected budget in lakhs or 'not_disclosed'",
                    "financing_status": "loan_required/cash_buyer/exploring_options",
                    "decision_timeline": "immediate/1-3months/3-6months/exploring"
                }},
                "property_requirements": {{
                    "property_type": "apartment/villa/plot/commercial/any",
                    "size_preference": "1bhk/2bhk/3bhk/4bhk+/flexible",
                    "location_preferences": ["location1", "location2"] or ["any"],
                    "key_amenities": ["amenity1", "amenity2"] or [],
                    "possession_preference": "ready_to_move/under_construction/any"
                }},
                "conversation_insights": {{
                    "pain_points": ["current housing issue1", "issue2"],
                    "motivation_factors": ["why buying now1", "factor2"],
                    "objections_concerns": ["concern1", "concern2"] or [],
                    "family_involvement": "self/spouse/parents/joint_decision"
                }},
                "next_actions": {{
                    "immediate_action": "send_properties/schedule_call/site_visit/nurture",
                    "follow_up_timeline": "same_day/tomorrow/3days/1week",
                    "recommended_properties": "matching property types to show",
                    "additional_info_needed": ["info1", "info2"] or []
                }},
                "agent_coaching": {{
                    "conversation_quality": "excellent/good/average/poor",
                    "missed_opportunities": ["opportunity1", "opportunity2"] or [],
                    "suggested_questions": ["question1", "question2"],
                    "closing_techniques": "technique to use for next interaction"
                }}
            }}
            """}
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=800,
            temperature=0.3
        )
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            analysis["industry"] = "real_estate"
            analysis["timestamp"] = context.get("timestamp")
            return analysis
        except json.JSONDecodeError:
            return self._fallback_real_estate_analysis()
    
    def generate_response_script(self, analysis: Dict[str, Any], industry: str) -> str:
        """Generate suggested response script for the agent"""
        try:
            if industry == "sales":
                if analysis.get("objection_handling", {}).get("objection_detected") != "none":
                    return analysis["objection_handling"]["recommended_response"]
                elif analysis.get("coaching_insights", {}).get("discovery_questions"):
                    questions = analysis["coaching_insights"]["discovery_questions"]
                    return f"Try asking: '{questions[0]}'"
                else:
                    return analysis.get("coaching_insights", {}).get("immediate_suggestion", "Continue exploring their needs.")
            
            elif industry == "real_estate":
                action = analysis.get("next_actions", {}).get("immediate_action", "continue")
                if action == "site_visit":
                    return "Let's schedule a site visit. Are you available this weekend to see the property?"
                elif action == "send_properties":
                    return "Based on your requirements, I have some excellent options. Can I send you the details?"
                elif action == "schedule_call":
                    return "Let me get more details about your preferences. When would be a good time for a detailed discussion?"
                else:
                    suggested_questions = analysis.get("agent_coaching", {}).get("suggested_questions", [])
                    return suggested_questions[0] if suggested_questions else "Tell me more about your ideal property."
            
        except Exception as e:
            self.logger.error(f"Response generation error: {e}")
        
        return "Please continue sharing your requirements."
    
    def _fallback_sales_analysis(self) -> Dict[str, Any]:
        return {
            "industry": "sales",
            "coaching_insights": {"immediate_suggestion": "Focus on understanding customer needs"},
            "deal_progression": {"progression_score": "5", "next_best_action": "Ask discovery questions"}
        }
    
    def _fallback_real_estate_analysis(self) -> Dict[str, Any]:
        return {
            "industry": "real_estate",
            "lead_qualification": {"quality_score": "5", "conversion_probability": "medium"},
            "next_actions": {"immediate_action": "continue_qualification"}
        }
    
    def _generic_analysis(self, transcript: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "industry": "general",
            "insights": ["Continue conversation naturally"],
            "next_actions": ["Ask clarifying questions"]
        }
    
    def _fallback_response(self, industry: str) -> Dict[str, Any]:
        return {
            "industry": industry,
            "error": "Analysis temporarily unavailable",
            "suggestion": "Continue conversation naturally"
        }
