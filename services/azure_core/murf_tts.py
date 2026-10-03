import os
import logging
import requests
import json
from typing import Optional, Dict, Any, Generator
from murf import Murf
from dotenv import load_dotenv

load_dotenv()

class EnhancedMurfTTSService:
    def __init__(self, api_key: Optional[str] = None):
        self.client = Murf(api_key=api_key or os.getenv("MURF_API_KEY"))
        self.logger = logging.getLogger(__name__)
        
        # Industry-optimized voice profiles showcasing Murf's capabilities
        self.voice_profiles = {
            "sales_coach_male": {
                "voice_id": "en-IN-rohan",
                "style": "Professional",
                "rate": 1.0,
                "pitch": 0,
                "variation": 1,
                "description": "Confident sales coaching voice"
            },
            "sales_coach_female": {
                "voice_id": "en-IN-alia", 
                "style": "Professional",
                "rate": 1.0,
                "pitch": 0,
                "variation": 1,
                "description": "Professional female sales coach"
            },
            "real_estate_consultant_male": {
                "voice_id": "en-IN-arjun",
                "style": "Conversational",
                "rate": 0.9,
                "pitch": 0,
                "variation": 2,
                "description": "Friendly property consultant"
            },
            "real_estate_consultant_female": {
                "voice_id": "en-IN-priya",
                "style": "Conversational", 
                "rate": 0.9,
                "pitch": 0,
                "variation": 2,
                "description": "Warm female property advisor"
            },
            "hindi_property_agent": {
                "voice_id": "hi-IN-kabir",
                "style": "Conversational",
                "rate": 0.85,
                "pitch": 0,
                "variation": 1,
                "description": "Hindi property consultant"
            },
            "customer_service_professional": {
                "voice_id": "en-IN-aarav",
                "style": "Friendly",
                "rate": 0.95,
                "pitch": 0, 
                "variation": 2,
                "description": "Professional customer service"
            }
        }
    
    def generate_voice_response(self, text: str, profile_name: str = "real_estate_consultant_male") -> bytes:
        """Generate high-quality voice using Murf AI with industry-specific optimization"""
        try:
            profile = self.voice_profiles.get(profile_name, self.voice_profiles["real_estate_consultant_male"])
            
            # Use Murf's advanced TTS capabilities
            response = self.client.text_to_speech.generate(
                text=text,
                voice_id=profile["voice_id"],
                style=profile["style"],
                rate=profile["rate"],
                pitch=profile["pitch"],
                variation=profile["variation"]
            )
            
            # Download the generated audio
            if hasattr(response, 'audio_file') and response.audio_file:
                audio_response = requests.get(response.audio_file, timeout=30)
                if audio_response.status_code == 200:
                    return audio_response.content
                else:
                    self.logger.error(f"Failed to download audio: {audio_response.status_code}")
            
            return b""
            
        except Exception as e:
            self.logger.error(f"Murf TTS generation error: {e}")
            return b""
    
    def create_industry_response(self, text: str, industry: str, gender: str = "male", language: str = "english") -> bytes:
        """Create voice responses optimized for specific industries"""
        
        # Select the best voice profile for the industry and context
        if industry == "sales":
            profile_name = f"sales_coach_{gender}"
        elif industry == "real_estate":
            if language == "hindi":
                profile_name = "hindi_property_agent" 
            else:
                profile_name = f"real_estate_consultant_{gender}"
        else:
            profile_name = "customer_service_professional"
        
        return self.generate_voice_response(text, profile_name)
    
    def create_welcome_message(self, industry: str, customer_name: str = "Customer", language: str = "english") -> bytes:
        """Create personalized welcome messages showcasing Murf's natural voice quality"""
        
        welcome_scripts = {
            "real_estate": {
                "english": f"""
                Hello {customer_name}! Thank you for your interest in our properties. 
                I'm here to help you find the perfect home or investment opportunity that matches your needs and budget.
                Do you have a few minutes to discuss your property requirements?
                """,
                "hindi": f"""
                नमस्ते {customer_name} जी! हमारी प्रॉपर्टी में आपकी दिलचस्पी के लिए धन्यवाद।
                मैं आपको आपकी जरूरत और बजट के अनुसार सबसे बेहतरीन घर या निवेश का अवसर खोजने में मदद करूंगा।
                क्या आपके पास अपनी प्रॉपर्टी की आवश्यकताओं पर चर्चा करने के लिए कुछ मिनट हैं?
                """
            },
            "sales": {
                "english": f"""
                Hi {customer_name}! I'm reaching out regarding your inquiry about our business solution.
                I'd love to understand your current challenges and explore how we can help drive growth for your organization.
                Is this a good time for a brief conversation about your business needs?
                """
            }
        }
        
        script = welcome_scripts.get(industry, {}).get(language, f"Hello {customer_name}! How can I assist you today?")
        return self.create_industry_response(script.strip(), industry, language=language)
    
    def create_property_presentation(self, property_details: Dict[str, Any], language: str = "english") -> bytes:
        """Create engaging property presentations demonstrating Murf's persuasive capabilities"""
        
        if language == "hindi":
            script = f"""
            मैं आपको {property_details.get('name', 'एक बेहतरीन प्रॉपर्टी')} के बारे में बताना चाहूंगा
            जो {property_details.get('location', 'प्रमुख स्थान')} में स्थित है।
            
            यह एक {property_details.get('type', 'आवासीय प्रॉपर्टी')} है 
            जिसकी कीमत {property_details.get('price', 'प्रतिस्पर्धी दर')} है।
            
            इसकी मुख्य विशेषताओं में {', '.join(property_details.get('amenities', ['आधुनिक सुविधाएं'])[:3])} शामिल हैं।
            
            क्या आप पेमेंट प्लान और साइट विजिट के विकल्पों के बारे में जानना चाहेंगे?
            """
        else:
            script = f"""
            I'd like to tell you about {property_details.get('name', 'an exceptional property')} 
            located in {property_details.get('location', 'a prime area')}.
            
            This is a {property_details.get('type', 'residential property')} 
            priced at {property_details.get('price', 'competitive rates')}.
            
            The key highlights include {', '.join(property_details.get('amenities', ['modern amenities'])[:3])}.
            
            The location offers excellent connectivity and strong appreciation potential.
            Would you like to know more about the payment plans and schedule a site visit?
            """
        
        return self.create_industry_response(script.strip(), "real_estate", language=language)
    
    def create_objection_response(self, objection_type: str, industry: str, context: Dict[str, Any] = None) -> bytes:
        """Generate contextual objection responses showcasing Murf's persuasive tone"""
        
        objection_responses = {
            "real_estate": {
                "price": """
                I completely understand that price is a key consideration. 
                Let me put this in perspective - this property offers exceptional value when you consider 
                the prime location, quality construction, and amenities. 
                
                Plus, property prices in this area have appreciated by 15% annually. 
                We also have flexible payment plans that can work with your budget.
                
                Would you like me to explain our easy EMI options?
                """,
                "location": """
                That's a great question about the location. 
                This area is strategically positioned with excellent connectivity - 
                the upcoming metro line will be operational next year, 
                and major IT hubs are just 20 minutes away.
                
                We're also seeing significant infrastructure development with new schools, 
                hospitals, and shopping centers coming up.
                
                Would you like me to share the detailed location advantages?
                """,
                "timing": """
                I appreciate you taking time to make this important decision.
                However, I should mention that property prices are increasing monthly,
                and we have limited units available at current rates.
                
                The good news is, you can secure this property with just a small token amount
                and take time for the final decision.
                
                This way, you won't miss out on both the property and the current pricing.
                Shall I check the token amount options for you?
                """
            },
            "sales": {
                "price": """
                I understand budget is always a critical factor in business decisions.
                Let me show you the complete picture - our solution typically delivers 
                300% ROI within the first year through efficiency gains and cost savings.
                
                Most of our clients find that the solution pays for itself within 6 months.
                We can also discuss flexible payment terms that align with your cash flow.
                
                Would you like to see a customized ROI calculation for your business?
                """,
                "features": """
                That's an excellent question about the features.
                Our solution is specifically designed for Indian businesses, 
                with built-in compliance for local regulations and 24/7 local support.
                
                What sets us apart is our implementation approach - 
                we ensure smooth transition with minimal disruption to your operations.
                
                Which specific features are most important for your business requirements?
                """,
                "competition": """
                It's smart that you're evaluating different options.
                What makes us unique is our deep understanding of the Indian market 
                and our track record of successful implementations.
                
                Our clients choose us because of our local support, 
                faster implementation, and proven results.
                
                Would you like to speak with a client in a similar business to hear their experience?
                """
            }
        }
        
        response_text = objection_responses.get(industry, {}).get(objection_type, 
            "I understand your concern. Let me address that based on your specific situation.")
        
        return self.create_industry_response(response_text.strip(), industry)
    
    def create_coaching_prompt(self, coaching_suggestion: str, urgency: str = "medium") -> bytes:
        """Create coaching audio prompts for sales reps"""
        
        urgency_prefixes = {
            "high": "URGENT: ",
            "medium": "Suggestion: ",
            "low": "Consider: "
        }
        
        prompt_text = f"{urgency_prefixes.get(urgency, '')}{coaching_suggestion}"
        
        return self.create_industry_response(prompt_text, "sales")
    
    def get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """Return available voice profiles showcasing Murf's voice variety"""
        return {
            name: {
                "voice_id": profile["voice_id"],
                "style": profile["style"], 
                "description": profile["description"],
                "best_for": name.split('_')[0]
            }
            for name, profile in self.voice_profiles.items()
        }
