import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class CompetitorIntelligence:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Competitor battle cards database
        self.battle_cards = {
            "salesforce": {
                "company_name": "Salesforce",
                "category": "CRM Platform",
                "strengths": ["Market leader", "Extensive features", "Strong ecosystem"],
                "weaknesses": ["High cost", "Complex implementation", "Over-engineered for SMBs"],
                "differentiators": {
                    "pricing": "We're 60% more cost-effective with faster ROI",
                    "implementation": "Our implementation takes 2 weeks vs their 3-6 months",
                    "ease_of_use": "Our interface is designed for Indian businesses",
                    "support": "24/7 local support vs their limited timezone coverage"
                },
                "common_objections": {
                    "feature_parity": "While Salesforce has more features, 80% are unused by most companies. We focus on features that actually drive results.",
                    "market_share": "Market share doesn't equal best fit. Our solution is specifically designed for Indian SMBs and delivers faster results."
                },
                "positioning_strategy": "Position as the practical, cost-effective alternative that delivers faster value",
                "proof_points": [
                    "3x faster implementation time",
                    "40% lower total cost of ownership",
                    "95% user adoption rate vs industry average of 60%"
                ]
            },
            "hubspot": {
                "company_name": "HubSpot",
                "category": "Inbound Marketing & CRM",
                "strengths": ["Good free tier", "Marketing focus", "User-friendly"],
                "weaknesses": ["Limited customization", "Expensive scaling", "Weak Indian localization"],
                "differentiators": {
                    "localization": "Built for Indian compliance and business practices",
                    "customization": "Highly customizable to match your exact workflow",
                    "pricing": "Transparent pricing without hidden costs",
                    "integration": "Seamless integration with Indian payment gateways and tools"
                },
                "common_objections": {
                    "free_tier": "Free is great for startups, but growing businesses need advanced features, automation, and support - that's where we excel.",
                    "marketing_features": "HubSpot is marketing-heavy. We provide balanced sales and marketing capabilities with better ROI tracking."
                },
                "positioning_strategy": "Position as the comprehensive, localized solution for serious businesses",
                "proof_points": [
                    "Indian compliance built-in",
                    "50% better conversion tracking",
                    "Local payment gateway integrations"
                ]
            },
            "zoho": {
                "company_name": "Zoho",
                "category": "Business Software Suite",
                "strengths": ["Indian company", "Affordable", "Wide product range"],
                "weaknesses": ["Fragmented experience", "Limited advanced features", "Poor integrations"],
                "differentiators": {
                    "focus": "We specialize in sales excellence while they try to do everything",
                    "user_experience": "Unified, intuitive interface vs their fragmented suite",
                    "advanced_features": "AI-powered insights and automation built-in",
                    "performance": "Faster, more reliable platform architecture"
                },
                "common_objections": {
                    "local_company": "Being Indian is great, but execution matters. We combine local understanding with global best practices and superior technology.",
                    "price_advantage": "Zoho seems cheaper upfront, but when you factor in the additional apps needed and productivity losses, we're actually more cost-effective."
                },
                "positioning_strategy": "Position as the specialized, high-performance alternative",
                "proof_points": [
                    "40% higher user productivity",
                    "Single login for all features vs multiple Zoho apps",
                    "99.9% uptime vs their reported downtimes"
                ]
            }
        }
        
        # Real estate competitor database
        self.real_estate_competitors = {
            "99acres": {
                "company_name": "99acres",
                "category": "Property Portal",
                "strengths": ["Large inventory", "Brand recognition", "Wide reach"],
                "weaknesses": ["Poor lead quality", "High competition", "Limited personalization"],
                "differentiators": {
                    "lead_quality": "We provide pre-qualified, serious leads vs their bulk inquiries",
                    "personalization": "Personalized property recommendations based on detailed profiling",
                    "support": "Dedicated relationship manager vs their automated responses",
                    "exclusive_properties": "Access to exclusive pre-launch and off-market properties"
                }
            },
            "magicbricks": {
                "company_name": "MagicBricks",
                "category": "Property Portal",
                "strengths": ["Market presence", "Mobile app", "Various property types"],
                "weaknesses": ["Spam leads", "Poor filtering", "Generic experience"],
                "differentiators": {
                    "lead_verification": "Every lead is verified and qualified before sharing",
                    "expert_guidance": "Property investment experts guide the entire process",
                    "end_to_end": "Complete transaction support from search to registration",
                    "investment_advice": "ROI analysis and market insights for investors"
                }
            }
        }
    
    def get_battle_card(self, competitor_name: str, industry: str = "sales") -> Optional[Dict[str, Any]]:
        """Retrieve battle card for specific competitor"""
        try:
            competitor_key = competitor_name.lower().replace(" ", "").replace("-", "")
            
            if industry == "sales":
                battle_cards_db = self.battle_cards
            elif industry == "real_estate":
                battle_cards_db = self.real_estate_competitors
            else:
                return None
            
            # Find matching competitor
            for key, card in battle_cards_db.items():
                if (competitor_key in key or 
                    competitor_key in card["company_name"].lower().replace(" ", "")):
                    return card
            
            return None
            
        except Exception as e:
            self.logger.error(f"Battle card retrieval error: {e}")
            return None
    
    def generate_competitive_response(self, competitor_name: str, objection_context: str, industry: str = "sales") -> Dict[str, Any]:
        """Generate competitive positioning response"""
        battle_card = self.get_battle_card(competitor_name, industry)
        
        if not battle_card:
            return {
                "competitor": competitor_name,
                "response": f"I understand you're evaluating {competitor_name}. Let me explain what makes our solution unique and why our clients choose us over alternatives.",
                "talking_points": [
                    "Focus on your specific requirements and business outcomes",
                    "Our proven track record with similar businesses",
                    "Comprehensive support and implementation process"
                ],
                "proof_points": ["Customer success stories", "ROI case studies", "Implementation timeline"]
            }
        
        # Generate contextual response based on objection
        response_strategy = self._determine_response_strategy(objection_context, battle_card)
        
        return {
            "competitor": battle_card["company_name"],
            "positioning_strategy": battle_card["positioning_strategy"],
            "response": response_strategy["response"],
            "talking_points": response_strategy["talking_points"],
            "differentiators": battle_card["differentiators"],
            "proof_points": battle_card["proof_points"],
            "handle_objections": battle_card.get("common_objections", {}),
            "next_steps": response_strategy["next_steps"]
        }
    
    def _determine_response_strategy(self, objection_context: str, battle_card: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the best response strategy based on context"""
        context_lower = objection_context.lower()
        
        # Price objection
        if any(word in context_lower for word in ["price", "cost", "expensive", "budget"]):
            return {
                "response": f"I understand cost is important. While {battle_card['company_name']} might seem competitive initially, let me show you the total cost of ownership and ROI.",
                "talking_points": [
                    battle_card["differentiators"].get("pricing", "Better value proposition"),
                    "Faster implementation = quicker ROI",
                    "Lower training and adoption costs"
                ],
                "next_steps": ["Provide detailed ROI calculation", "Share cost comparison analysis"]
            }
        
        # Feature comparison
        elif any(word in context_lower for word in ["features", "functionality", "capabilities"]):
            return {
                "response": f"{battle_card['company_name']} has many features, but more isn't always better. Let me show you how our focused approach delivers better results.",
                "talking_points": [
                    "Quality over quantity in feature set",
                    "Features that actually get used vs shelf-ware",
                    "Better user experience and adoption"
                ],
                "next_steps": ["Demo key differentiating features", "Show user adoption statistics"]
            }
        
        # Market position / brand
        elif any(word in context_lower for word in ["market leader", "bigger company", "brand"]):
            return {
                "response": f"You're right that {battle_card['company_name']} is well-known. However, being the best fit for your specific needs is what really matters.",
                "talking_points": [
                    battle_card["positioning_strategy"],
                    "Specialized focus vs trying to be everything to everyone",
                    "Better customer service and responsiveness"
                ],
                "next_steps": ["Arrange customer reference call", "Share customer success stories"]
            }
        
        # General comparison
        else:
            return {
                "response": f"Great question about {battle_card['company_name']}. Let me highlight what makes us different and why our clients chose us.",
                "talking_points": list(battle_card["differentiators"].values())[:3],
                "next_steps": ["Provide detailed comparison document", "Schedule follow-up to address specific concerns"]
            }
    
    def detect_competitor_mention(self, transcript: str, industry: str = "sales") -> Optional[str]:
        """Detect competitor mentions in conversation"""
        transcript_lower = transcript.lower()
        
        if industry == "sales":
            competitors_db = self.battle_cards
        elif industry == "real_estate":
            competitors_db = self.real_estate_competitors
        else:
            return None
        
        # Check for competitor mentions
        for competitor_key, battle_card in competitors_db.items():
            company_name = battle_card["company_name"].lower()
            
            # Direct name mention
            if company_name in transcript_lower:
                return battle_card["company_name"]
            
            # Partial matches
            name_parts = company_name.split()
            if len(name_parts) > 1 and any(part in transcript_lower for part in name_parts if len(part) > 3):
                return battle_card["company_name"]
            
            # Common abbreviations or alternate names
            if competitor_key in ["salesforce"] and any(term in transcript_lower for term in ["sf", "sfdc"]):
                return battle_card["company_name"]
            elif competitor_key in ["hubspot"] and "hub spot" in transcript_lower:
                return battle_card["company_name"]
        
        return None
    
    def add_custom_battle_card(self, competitor_data: Dict[str, Any], industry: str = "sales") -> Dict[str, str]:
        """Add custom competitor battle card"""
        try:
            competitor_key = competitor_data["company_name"].lower().replace(" ", "").replace("-", "")
            
            if industry == "sales":
                self.battle_cards[competitor_key] = competitor_data
            elif industry == "real_estate":
                self.real_estate_competitors[competitor_key] = competitor_data
            
            return {
                "status": "success",
                "message": f"Battle card added for {competitor_data['company_name']}"
            }
        
        except Exception as e:
            self.logger.error(f"Battle card addition error: {e}")
            return {
                "status": "error", 
                "message": str(e)
            }
    
    def get_industry_competitive_landscape(self, industry: str = "sales") -> Dict[str, Any]:
        """Get overview of competitive landscape for industry"""
        if industry == "sales":
            competitors_db = self.battle_cards
        elif industry == "real_estate":
            competitors_db = self.real_estate_competitors
        else:
            return {"error": "Industry not supported"}
        
        landscape = {
            "total_competitors": len(competitors_db),
            "categories": {},
            "common_differentiators": {},
            "top_objections": []
        }
        
        # Analyze categories
        for competitor in competitors_db.values():
            category = competitor.get("category", "Unknown")
            if category not in landscape["categories"]:
                landscape["categories"][category] = 0
            landscape["categories"][category] += 1
        
        # Extract common differentiators
        all_differentiators = []
        for competitor in competitors_db.values():
            all_differentiators.extend(competitor.get("differentiators", {}).keys())
        
        # Count frequency of differentiators
        diff_counts = {}
        for diff in all_differentiators:
            diff_counts[diff] = diff_counts.get(diff, 0) + 1
        
        landscape["common_differentiators"] = dict(sorted(diff_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return landscape
