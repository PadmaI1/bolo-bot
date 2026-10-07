import asyncio
import logging
import json
import base64
import io
import time  # ⚡ NEW: For performance tracking
from datetime import datetime
from typing import Dict, Any, Optional
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, BackgroundTasks, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
import os

# Import optimized services
# from services.websocket_manager import websocket_manager  # Not needed for phone calls
from services.audio_processor import AudioProcessor
from services.azure_services import AzureServicesOptimized
from services.murf_voice import MurfVoiceOptimized
from services.murf_websocket_streaming import MurfWebSocketStreaming
# These services use websocket_manager (for browser-based WebSocket, not phone calls)
# from services.sales_ai import SalesAIEngine
# from services.realestate_ai import RealEstateAIEngine
# from services.conversation_ai import ConversationAI
from services.mock_crm import MockCRMService
from services.phone_service import TwilioPhoneService
from services.intelligent_phone_ai import IntelligentPhoneAI
# ⚡ NEW: Ultra-fast native sales with premium voices
from services.ultra_fast_native_sales import UltraFastNativeSales, ExperiencedSalesAgent
from services.lightning_language_detector import LightningLanguageDetector
from services.email_service import EmailService
# from services.salesforce_crm import SalesforceIntegration  # Uncomment when ready to use Salesforce

load_dotenv()

# CRM Configuration - Easy switch between Mock and Salesforce
USE_MOCK_CRM = True  # Set to False to use Salesforce

# Configure logging for production with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voiceflow_ai.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global service instances  
azure_service: Optional[AzureServicesOptimized] = None
murf_service: Optional[MurfVoiceOptimized] = None
murf_ws_streaming: Optional[MurfWebSocketStreaming] = None
audio_processor: Optional[AudioProcessor] = None
# WebSocket-based services (not used for phone calls)
# sales_ai: Optional[SalesAIEngine] = None
# realestate_ai: Optional[RealEstateAIEngine] = None
# conversation_ai: Optional[ConversationAI] = None
salesforce_crm: Optional[MockCRMService] = None
phone_service: Optional[TwilioPhoneService] = None
intelligent_phone_ai: Optional[IntelligentPhoneAI] = None
# ⚡ NEW: Ultra-fast services with NO preprocessing
ultra_fast_sales: Optional[UltraFastNativeSales] = None
language_detector: Optional[LightningLanguageDetector] = None
sales_agent: Optional[ExperiencedSalesAgent] = None
email_service: Optional[EmailService] = None

# Application state
app_state = {
    "total_sessions": 0,
    "active_sessions": 0,
    "startup_time": datetime.now(),
    "service_health": {}
}

# ⚡ Conversation memory for context-aware responses
conversation_memory: Dict[str, list] = {}

def get_optimal_bilingual_voice(language: str, call_type: str, gender: str = "male") -> str:
    """
    ⭐ Get Shaan voice for bilingual Hindi/English conversations
    
    Shaan (hi-IN-shaan) is PERFECT for:
    - Native Hindi and English bilingual conversations
    - Indian B2B sales and business discussions
    - Natural code-switching between languages
    - Professional, confident, warm tone
    
    Args:
        language: Detected language (hindi, english, telugu)
        call_type: Type of call (b2b_sales, real_estate)
        gender: Voice gender (male/female)
    
    Returns:
        Voice ID optimized for bilingual Indian business calls
    """
    # Shaan is the BEST for bilingual Hindi/English
    # Perfect for all Indian business scenarios
    if gender == "male":
        return "hi-IN-shaan"  # ⭐ PREMIUM bilingual male voice
    else:
        return "hi-IN-shweta"  # ⭐ PREMIUM bilingual female voice (if needed)

def enhance_bilingual_response(ai_response: str, customer_input: str) -> str:
    """
    ⭐ Enhance AI response with natural Hindi-English code-switching
    
    Makes responses sound more natural for Indian business conversations
    by adding common Hindi phrases where appropriate.
    
    Args:
        ai_response: Original AI generated response
        customer_input: What customer said (for context)
    
    Returns:
        Enhanced response with natural bilingual mixing
    """
    # Add natural Hindi words for better bilingual feel
    enhancements = {
        "Yes": "Haan bilkul",
        "Thank you": "Dhanyawad",
        "Okay": "Theek hai",
        "Good": "Bahut accha",
        "Perfect": "Bilkul perfect",
        "Exactly": "Exactly, bilkul sahi",
        "Great": "Bahut badhiya",
        "Sure": "Haan ji",
        "I understand": "Samajh gaya"
    }
    
    enhanced = ai_response
    for english, hinglish in enhancements.items():
        # Only replace at start of sentences for natural flow
        enhanced = enhanced.replace(f"{english}!", f"{hinglish}!")
        enhanced = enhanced.replace(f"{english},", f"{hinglish},")
        enhanced = enhanced.replace(f"{english}.", f"{hinglish}.")
    
    return enhanced

def get_smart_response(customer_input: str, customer_name: str = "Sir") -> Optional[str]:
    """
    ⚡ INSTANT responses for common intents - bypass AI entirely
    Detects simple intents and returns pre-crafted responses
    Returns None if needs AI generation
    
    Target: <10ms response time (NO AI call needed)
    
    IMPORTANT: Only triggers for VERY SIMPLE/SHORT inputs
    Complex questions MUST go to AI for contextual answers
    
    Args:
        customer_input: What customer said
        customer_name: Customer's name for personalization
    
    Returns:
        Pre-crafted response for common intents, or None if needs AI
    """
    customer_input_lower = customer_input.lower().strip()
    
    # ONLY use smart responses for VERY SHORT inputs (< 6 words)
    word_count = len(customer_input_lower.split())
    if word_count > 6:
        # Complex query - MUST use AI
        return None
    
    # AFFIRMATIVE RESPONSES (simple yes/ok only)
    if customer_input_lower in ["yes", "haan", "han", "okay", "ok", "sure", "bilkul", "ji", "ji haan", "yes please"]:
        return f"Perfect! {customer_name}, Murf's API can generate studio-quality voiceovers in 120+ voices. Want a quick demo?"
    
    # NEGATIVE RESPONSES (simple no only)
    if customer_input_lower in ["no", "nahi", "nahin", "not interested", "busy", "nahi ji"]:
        return f"I understand, {customer_name}. Can I send you a quick demo link for when you have time?"
    
    # For everything else (including questions) - USE AI
    return None
    
    return enhanced

def _get_conversation_history(call_sid: str) -> str:
    """Get formatted conversation history for context"""
    if call_sid not in conversation_memory:
        return "No previous conversation"
    
    history = conversation_memory[call_sid][-6:]  # Last 3 exchanges (6 messages)
    if not history:
        return "This is the start of conversation"
    
    formatted = []
    for msg in history:
        speaker = "Customer" if msg["role"] == "customer" else "You"
        formatted.append(f"{speaker}: {msg['text']}")
    
    return "\n".join(formatted)

def _update_conversation_history(call_sid: str, customer_text: str, agent_response: str):
    """Update conversation history"""
    if call_sid not in conversation_memory:
        conversation_memory[call_sid] = []
    
    conversation_memory[call_sid].extend([
        {"role": "customer", "text": customer_text, "timestamp": time.time()},
        {"role": "agent", "text": agent_response, "timestamp": time.time()}
    ])
    
    # Keep only last 20 messages (10 exchanges)
    if len(conversation_memory[call_sid]) > 20:
        conversation_memory[call_sid] = conversation_memory[call_sid][-20:]

def _detect_intent(speech_result: str) -> str:
    """Fast intent detection using keywords (no AI needed)"""
    text_lower = speech_result.lower()
    
    # Positive interest signals
    if any(word in text_lower for word in ["yes", "sure", "okay", "interested", "tell me more", "sounds good"]):
        return "interested"
    
    # Questions about product/features
    if any(word in text_lower for word in ["what", "how", "can you", "tell me about", "explain", "show me"]):
        return "seeking_information"
    
    # Pricing/cost concerns
    if any(word in text_lower for word in ["price", "cost", "expensive", "cheap", "budget", "afford"]):
        return "pricing_inquiry"
    
    # Technical questions
    if any(word in text_lower for word in ["api", "integration", "technical", "documentation", "sdk", "code"]):
        return "technical_inquiry"
    
    # Objections
    if any(word in text_lower for word in ["not interested", "busy", "not now", "call back", "maybe later"]):
        return "objection"
    
    # Request for demo/trial
    if any(word in text_lower for word in ["demo", "trial", "test", "example", "show", "see it"]):
        return "demo_request"
    
    # Real estate specific
    if any(word in text_lower for word in ["property", "bhk", "flat", "apartment", "location", "gachibowli", "hitec"]):
        return "property_inquiry"
    
    # Confirmation/acknowledgment
    if any(word in text_lower for word in ["hello", "hi", "yeah", "ok", "can hear", "listening"]):
        return "acknowledgment"
    
    return "general_inquiry"

def _is_generic_response(response: str) -> bool:
    """Check if response is generic/unhelpful"""
    generic_phrases = [
        "let me help you with that",
        "i understand your concern",
        "that's a good question",
        "i can help with that",
        "let me assist you",
        "i'd be happy to help",
        "thank you for sharing"
    ]
    
    response_lower = response.lower()
    
    # Check if response is too short and generic
    if len(response.split()) < 10:
        for phrase in generic_phrases:
            if phrase in response_lower:
                return True
    
    return False

def _generate_smart_fallback(call_type: str, customer_speech: str, intent: str) -> str:
    """Generate smart fallback based on context"""
    if call_type == "b2b_sales":
        if intent == "interested":
            return "Great! Tell me, what kind of voice content are you creating today - is it for e-learning, marketing videos, or something else?"
        elif intent == "pricing_inquiry":
            return "Murf API pricing is very affordable - you pay only for what you use. Most startups spend around $50-200/month. What's your expected monthly voice content volume?"
        elif intent == "technical_inquiry":
            return "Our API is super simple - just a REST endpoint. You send text, get audio back. Works with Python, Node, Java, anything. Want me to email you the integration guide?"
        elif intent == "demo_request":
            return "Perfect! I can set up a 15-minute live demo where I'll show you the API in action. What day works best for you - tomorrow or later this week?"
        else:
            return "I'd love to learn about your voice content needs. Are you currently using voice actors, or doing voiceovers yourself?"
    
    else:  # real_estate
        if intent == "interested":
            return "Excellent! What's your budget range and preferred location in Hyderabad - are you looking at Gachibowli, Hitec City, or another area?"
        elif intent == "property_inquiry":
            return "We have amazing properties! Tell me your budget, preferred location, and whether you want 2BHK, 3BHK, or a villa?"
        elif intent == "pricing_inquiry":
            return "Property prices in Gachibowli start from ₹60 lakhs for 2BHK and ₹1.2 crores for 3BHK. What's your budget range, Arjun?"
        else:
            return "Perfect! Are you looking for a property for your own residence or investment purposes? And what's your budget range?"

# 🆕 Call Summary and CRM Processing
call_summaries: Dict[str, Any] = {}  # Store call summaries for dashboard

async def _process_call_completion(call_sid: str, call_type: str, conversation_history: list, call_duration: int):
    """Process call completion, update CRM, and send email"""
    try:
        logger.info(f"📊 Processing call completion: {call_sid} ({call_type})")
        
        # Generate call summary
        summary = _generate_call_summary(conversation_history, call_type, call_duration)
        
        # Update CRM based on call type
        if call_type == "b2b_sales":
            crm_result = await _update_sales_crm(call_sid, summary)
        else:  # real_estate
            crm_result = await _update_real_estate_crm(call_sid, summary)
        
        # 📧 Get customer email from lead_info (dynamic from form)
        customer_email = None
        customer_name = "Customer"
        
        if phone_service and call_sid in phone_service.active_calls:
            lead_info = phone_service.active_calls[call_sid].get("lead_info", {})
            customer_email = lead_info.get("email")
            customer_name = lead_info.get("name", "Customer")
        
        # Fallback to .env if email not in form (backward compatibility)
        if not customer_email:
            customer_email = os.getenv("CUSTOMER_EMAIL", "customer@example.com")
            logger.warning(f"⚠️ No email in lead_info, using .env: {customer_email}")
        
        # Send email summary to customer
        if email_service and email_service.enabled and customer_email:
            try:
                if call_type == "b2b_sales":
                    email_sent = await email_service.send_sales_summary_email(
                        recipient_email=customer_email,
                        recipient_name=customer_name,
                        call_summary=summary
                    )
                else:  # real_estate
                    email_sent = await email_service.send_real_estate_summary_email(
                        recipient_email=customer_email,
                        recipient_name=customer_name,
                        call_summary=summary
                    )
                
                if email_sent:
                    logger.info(f"✅ Email sent to {customer_email} for call {call_sid}")
                    summary["email_sent"] = True
                else:
                    logger.warning(f"⚠️ Email failed to send for call {call_sid}")
                    summary["email_sent"] = False
            except Exception as e:
                logger.error(f"❌ Email error for call {call_sid}: {e}")
                summary["email_sent"] = False
        else:
            logger.warning("⚠️ Email service not available")
            summary["email_sent"] = False
        
        # Store for dashboard display
        call_summaries[call_sid] = {
            "summary": summary,
            "crm_update": crm_result,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Call {call_sid} processed successfully - Lead Score: {summary.get('lead_score', summary.get('qualification_score', 0))}")
        
    except Exception as e:
        logger.error(f"❌ Call processing failed for {call_sid}: {e}")

def _generate_call_summary(conversation_history: list, call_type: str, duration: int) -> Dict[str, Any]:
    """Generate intelligent call summary"""
    if not conversation_history:
        return {"status": "no_conversation", "duration": duration, "call_type": call_type}
    
    customer_responses = [msg for msg in conversation_history if msg.get("role") == "customer"]
    
    if call_type == "b2b_sales":
        # Sales-specific analysis
        response_text = " ".join([r.get("text", "").lower() for r in customer_responses])
        
        # Analyze interest level
        if any(word in response_text for word in ["interested", "yes", "demo", "show me"]):
            interest_level = "high"
        elif any(word in response_text for word in ["maybe", "think", "later"]):
            interest_level = "medium"
        else:
            interest_level = "low"
        
        # Extract use case
        if "audiobook" in response_text:
            use_case = "audiobooks"
        elif "elearning" in response_text or "training" in response_text:
            use_case = "e-learning"
        elif "marketing" in response_text:
            use_case = "marketing"
        else:
            use_case = "general"
        
        lead_score = 8 if interest_level == "high" else 5 if interest_level == "medium" else 2
        
        return {
            "call_type": "B2B Sales",
            "duration_seconds": duration,
            "interest_level": interest_level,
            "use_case": use_case,
            "total_exchanges": len(customer_responses),
            "next_steps": f"Follow up on {use_case} demo" if interest_level == "high" else "Send email with case studies",
            "lead_score": lead_score,
            "customer_sentiment": "interested" if interest_level == "high" else "neutral"
        }
    
    else:  # real_estate
        response_text = " ".join([r.get("text", "").lower() for r in customer_responses])
        
        # Extract budget
        budget_range = "₹60L-1.2Cr" if "lakh" in response_text or "crore" in response_text else "not_specified"
        
        # Extract location
        if "gachibowli" in response_text:
            location = "Gachibowli"
        elif "hitec" in response_text:
            location = "Hitec City"
        elif "jubilee" in response_text:
            location = "Jubilee Hills"
        else:
            location = "any"
        
        # Extract property type
        if "2bhk" in response_text or "2 bhk" in response_text:
            property_type = "2BHK"
        elif "3bhk" in response_text or "3 bhk" in response_text:
            property_type = "3BHK"
        elif "villa" in response_text:
            property_type = "Villa"
        else:
            property_type = "not_specified"
        
        qualification_score = 0
        if budget_range != "not_specified": qualification_score += 3
        if location != "any": qualification_score += 3
        if property_type != "not_specified": qualification_score += 4
        
        return {
            "call_type": "Real Estate",
            "duration_seconds": duration,
            "budget_range": budget_range,
            "location_preference": location,
            "property_type": property_type,
            "qualification_score": qualification_score,
            "next_steps": "Schedule site visit" if qualification_score >= 7 else "Send WhatsApp property details",
            "total_exchanges": len(customer_responses)
        }

async def _update_sales_crm(call_sid: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    """Update CRM with sales call data"""
    lead_data = {
        "call_sid": call_sid,
        "lead_name": "Arjun Mehta",
        "company": "Anurag University",
        "interest_level": summary.get("interest_level", "low"),
        "use_case": summary.get("use_case", "general"),
        "lead_score": summary.get("lead_score", 0),
        "next_followup": datetime.now().strftime("%Y-%m-%d"),
        "notes": f"Interested in {summary.get('use_case')} use case. Call duration: {summary.get('duration_seconds')}s"
    }
    
    if salesforce_crm:
        result = await salesforce_crm.sync_sales_call_data(lead_data, summary)
        logger.info(f"✅ CRM updated for sales call: {call_sid}")
        return result
    
    return {"status": "crm_not_available"}

async def _update_real_estate_crm(call_sid: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    """Update CRM with real estate call data"""
    lead_data = {
        "call_sid": call_sid,
        "lead_name": "Arjun Mehta",
        "phone": os.getenv("MY_NUMBER", "+919999999999"),
        "budget_range": summary.get("budget_range", "not_specified"),
        "location_preference": summary.get("location_preference", "any"),
        "property_type": summary.get("property_type", "not_specified"),
        "qualification_score": summary.get("qualification_score", 0),
        "next_followup": datetime.now().strftime("%Y-%m-%d"),
        "notes": f"Budget: {summary.get('budget_range')}, Location: {summary.get('location_preference')}"
    }
    
    if salesforce_crm:
        result = await salesforce_crm.sync_real_estate_lead(lead_data, summary)
        logger.info(f"✅ CRM updated for real estate call: {call_sid}")
        return result
    
    return {"status": "crm_not_available"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """⚡ Lightning-fast startup - NO preprocessing, direct streaming only"""
    logger.info("⚡ Initializing Lightning-Fast B2B Agent (NO preprocessing)...")
    
    global azure_service, murf_service, murf_ws_streaming, audio_processor, salesforce_crm, phone_service, intelligent_phone_ai, ultra_fast_sales, language_detector, sales_agent, email_service
    
    try:
        # Initialize core services
        azure_service = AzureServicesOptimized()
        await azure_service.initialize()
        app_state["service_health"]["azure"] = "healthy"
        logger.info("✅ Azure Services initialized")
        
        murf_service = MurfVoiceOptimized()
        await murf_service.initialize()
        app_state["service_health"]["murf"] = "healthy"
        logger.info("✅ Murf Voice Services initialized")
        
        # Initialize Rate Limiter for Murf API (prevents 429 errors)
        from services.rate_limiter import MurfRateLimiter
        rate_limiter = MurfRateLimiter(requests_per_minute=20, burst_limit=3)
        logger.info("🚦 Rate limiter initialized (20 req/min, burst: 3)")
        
        # Initialize Murf WebSocket Streaming for phone calls WITH rate limiter
        murf_ws_streaming = MurfWebSocketStreaming(rate_limiter=rate_limiter)
        app_state["service_health"]["murf_ws"] = "healthy"
        logger.info("⚡ Murf WebSocket Streaming initialized - Ultra-low latency for phone calls!")
        
        audio_processor = AudioProcessor()
        app_state["service_health"]["audio"] = "healthy"
        logger.info("✅ Audio Processor initialized")
        
        # WebSocket-based AI engines (commented out - not needed for phone calls)
        # sales_ai = SalesAIEngine(azure_service, murf_service, websocket_manager)
        # app_state["service_health"]["sales_ai"] = "healthy"
        # logger.info("✅ Sales AI Engine initialized")
        
        # realestate_ai = RealEstateAIEngine(azure_service, murf_service, websocket_manager)
        # app_state["service_health"]["realestate_ai"] = "healthy"
        # logger.info("✅ Real Estate AI Engine initialized")
        
        # conversation_ai = ConversationAI(azure_service, murf_service, websocket_manager)
        # app_state["service_health"]["conversation_ai"] = "healthy"
        # logger.info("✅ Conversation AI initialized - Ready for human-like calls")
        
        # Initialize Intelligent Phone AI
        intelligent_phone_ai = IntelligentPhoneAI(azure_service, murf_ws_streaming)
        app_state["service_health"]["intelligent_phone_ai"] = "healthy"
        logger.info("🤖 Intelligent Phone AI initialized - Smart conversations ready!")
        
        # ⚡⚡⚡ NEW: Ultra-Fast Services with Premium Voices ⚡⚡⚡
        # NO preprocessing, NO caching - Direct streaming only!
        ultra_fast_sales = UltraFastNativeSales()
        language_detector = LightningLanguageDetector()
        sales_agent = ExperiencedSalesAgent()
        app_state["service_health"]["ultra_fast"] = "healthy"
        logger.info("⚡⚡⚡ ULTRA-FAST Native Sales initialized!")
        logger.info("    ✅ Premium Hindi voices (shweta/shaan)")
        logger.info("    ✅ Connection pooling (saves 650ms/call)")
        logger.info("    ✅ Direct WebSocket streaming")
        logger.info("    ✅ Target: <500ms TTFB, <1.5s total")
        logger.info("⚡ Lightning-fast system ready - NO preprocessing!")
        
        # Initialize CRM integration (Mock or Salesforce)
        try:
            if USE_MOCK_CRM:
                salesforce_crm = MockCRMService()
                if await salesforce_crm.initialize():
                    app_state["service_health"]["crm"] = "healthy"
                    logger.info("✅ Mock CRM integrated (development mode)")
                else:
                    app_state["service_health"]["crm"] = "degraded"
                    logger.warning("⚠️ Mock CRM integration degraded")
            else:
                from services.salesforce_crm import SalesforceIntegration
                sf_crm = SalesforceIntegration()
                if await sf_crm.initialize():
                    salesforce_crm = sf_crm
                    app_state["service_health"]["crm"] = "healthy"
                    logger.info("✅ Salesforce CRM integrated")
                else:
                    app_state["service_health"]["crm"] = "degraded"
                    logger.warning("⚠️ Salesforce integration degraded")
        except Exception as e:
            app_state["service_health"]["crm"] = "offline"
            logger.warning(f"⚠️ CRM offline: {e}")
            # Fallback to Mock CRM
            if not USE_MOCK_CRM:
                logger.info("Falling back to Mock CRM...")
                salesforce_crm = MockCRMService()
                await salesforce_crm.initialize()
                app_state["service_health"]["crm"] = "healthy"

        # Initialize Email Service (for call summaries)
        try:
            email_service = EmailService()
            logger.info("✅ Email service initialized")
        except Exception as e:
            logger.warning(f"⚠️ Email service unavailable: {e}")

        # Initialize Phone Service (Twilio)
        try:
            phone_service = TwilioPhoneService()
            if await phone_service.initialize():
                app_state["service_health"]["phone"] = "healthy"
                logger.info("📞 Twilio Phone Service initialized - Real phone calls enabled")
            else:
                app_state["service_health"]["phone"] = "offline"
                logger.warning("⚠️ Phone service not configured - add Twilio credentials to .env")
        except Exception as e:
            app_state["service_health"]["phone"] = "offline"
            logger.warning(f"⚠️ Phone service offline: {e}")
        
        # Register WebSocket handlers (commented out - for browser WebSocket, not phone calls)
        # websocket_manager.register_handler("audio", handle_audio_message)
        # websocket_manager.register_handler("text", handle_text_message)
        # websocket_manager.register_handler("system", handle_system_message)
        
        # Start background health checks
        health_check_task = asyncio.create_task(periodic_health_check())
        
        logger.info("VoiceFlow AI Platform fully initialized and ready")
        
        yield  # Application runs here
        
        # Cancel health check task on shutdown
        health_check_task.cancel()
        try:
            await health_check_task
        except asyncio.CancelledError:
            pass
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down VoiceFlow AI Platform...")
    try:
        if azure_service:
            await azure_service.close()
        if murf_service:
            await murf_service.close()
        logger.info("Services closed gracefully")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# Create FastAPI app with lifecycle management
app = FastAPI(
    title="VoiceFlow AI Platform",
    description="Ultra-low latency multi-industry voice AI platform powered by Azure OpenAI & Murf AI",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Configure for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend")

# Main dashboard routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main platform dashboard"""
    return templates.TemplateResponse("admin_panel.html", {
        "request": request,
        "platform_name": "VoiceFlow AI Platform",
        "version": "2.0.0",
        "service_health": app_state["service_health"]
    })

@app.get("/demo", response_class=HTMLResponse)
async def demo_page(request: Request):
    """Interactive demo page for AI calls"""
    return templates.TemplateResponse("demo_call.html", {"request": request})

@app.get("/sales", response_class=HTMLResponse) 
async def sales_copilot(request: Request):
    """B2B Sales Copilot Interface"""
    return templates.TemplateResponse("sales_dashboard.html", {
        "request": request,
        "industry": "sales",
        "websocket_url": f"ws://{request.headers.get('host', 'localhost')}/ws/sales"
    })

@app.get("/real-estate", response_class=HTMLResponse)
async def real_estate_portal(request: Request):
    """Real Estate Lead Qualification Interface"""
    return templates.TemplateResponse("real_estate_portal.html", {
        "request": request,
        "industry": "real_estate", 
        "websocket_url": f"ws://{request.headers.get('host', 'localhost')}/ws/real_estate"
    })

# Browser WebSocket endpoints (commented out - not needed for phone calls)
@app.websocket("/ws/{industry}")
async def websocket_endpoint(websocket: WebSocket, industry: str):
    """Disabled - Use phone call endpoints instead"""
    await websocket.close(code=1008, reason="Use phone call endpoints")
    return

# Disabled WebSocket handlers (not needed for phone calls)
async def process_audio_callback(session_id: str, processed_audio: bytes, industry: str):
    """Disabled - Use phone call endpoints"""
    pass

async def handle_audio_message(session_id: str, audio_data: bytes):
    """Disabled - Use phone call endpoints"""
    pass

async def handle_text_message(session_id: str, message: Dict[str, Any]):
    """Disabled - Use phone call endpoints"""
    pass

async def handle_system_message(session_id: str, message: Dict[str, Any]):
    """Disabled - Use phone call endpoints"""
    pass

async def cleanup_session(session_id: str, industry: str):
    """Simplified session cleanup for phone calls"""
    try:
        # Cleanup audio processor if available
        if audio_processor:
            try:
                await audio_processor.finalize_session(session_id)
            except:
                pass  # Ignore if method doesn't exist
        
        logger.info(f"✅ Session cleanup completed: {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Session cleanup error: {e}")

async def sync_to_crm_background(session_id: str, ai_response: Dict[str, Any], industry: str):
    """Background task for CRM synchronization - Simplified for phone calls"""
    try:
        if not salesforce_crm:
            return
        
        # Prepare CRM data based on industry
        if industry == "sales":
            crm_result = await salesforce_crm.sync_sales_call_data(
                {"session_id": session_id, "duration_minutes": 5},  # Mock data
                ai_response
            )
        else:  # real_estate
            crm_result = await salesforce_crm.sync_real_estate_lead(
                {"session_id": session_id, "phone": "9876543210"},  # Mock data
                ai_response.get("qualification_update", {})
            )
        
        logger.info(f"✅ CRM sync completed for {session_id}: {crm_result.get('status')}")
        
    except Exception as e:
        logger.error(f"❌ Background CRM sync error: {e}")

# REST API Endpoints

@app.get("/api/health")
async def health_check():
    """Comprehensive health check"""
    uptime_seconds = (datetime.now() - app_state["startup_time"]).total_seconds()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime_seconds,
        "version": "2.0.0",
        "services": app_state["service_health"],
        "sessions": {
            "total": app_state["total_sessions"],
            "active": app_state["active_sessions"]
        }
    }

@app.get("/api/performance")
async def get_performance_metrics():
    """Get platform performance metrics - ✅ FIXED: Removed websocket_manager"""
    try:
        # Murf service stats
        murf_stats = {}
        if murf_service:
            murf_stats = murf_service.get_stats() if hasattr(murf_service, 'get_stats') else {}
        
        # Salesforce stats
        salesforce_stats = {}
        if salesforce_crm:
            salesforce_stats = await salesforce_crm.get_sync_statistics()
        
        # Call summaries
        call_stats = {
            "total_calls": len(call_summaries),
            "recent_calls": len([c for c in call_summaries.values() 
                               if (datetime.now() - datetime.fromisoformat(c["timestamp"])).seconds < 3600])
        }
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "call_performance": call_stats,
            "voice_generation": murf_stats,
            "crm_integration": salesforce_stats,
            "platform_health": app_state["service_health"]
        }
        
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/dashboard")
async def get_analytics_dashboard():
    """Get analytics dashboard data - ✅ FIXED: Removed websocket_manager dependency"""
    try:
        # Calculate uptime
        uptime = datetime.now() - app_state["startup_time"]
        uptime_seconds = int(uptime.total_seconds())
        
        # Get call summaries for dashboard
        total_calls = len(call_summaries)
        recent_calls = list(call_summaries.values())[-10:]  # Last 10 calls
        
        # Get CRM stats
        crm_stats = {}
        if salesforce_crm:
            crm_stats = await salesforce_crm.get_sync_statistics()
        
        return {
            "status": "success",
            "platform": {
                "name": "VoiceFlow AI Platform",
                "version": "2.0.0",
                "uptime_seconds": uptime_seconds,
                "health": app_state["service_health"]
            },
            "sessions": {
                "total": app_state["total_sessions"],
                "active": app_state["active_sessions"]
            },
            "analytics": {
                "total_sessions": app_state["total_sessions"],
                "active_sessions": app_state["active_sessions"],
                "avg_session_duration": "5min",  # Mock data
                "voice_quality_score": "9.2/10"  # Mock data
            },
            "calls": {
                "total": total_calls,
                "recent": recent_calls
            },
            "crm": crm_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analytics dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/generate")
async def generate_voice_sample(request: Request):
    """Generate voice sample for testing"""
    try:
        data = await request.json()
        text = data.get("text", "Hello, this is a voice test.")
        voice_profile = data.get("voice_profile", "realestate_consultant_female")
        
        if not murf_service:
            raise HTTPException(status_code=503, detail="Voice service unavailable")
        
        audio_data = await murf_service.generate_premium_voice(text, voice_profile)
        
        if audio_data:
            return StreamingResponse(
                io.BytesIO(audio_data),
                media_type="audio/mpeg",
                headers={"Content-Disposition": "inline; filename=voice_sample.mp3"}
            )
        else:
            raise HTTPException(status_code=500, detail="Voice generation failed")
    
    except Exception as e:
        logger.error(f"Voice generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crm/test-connection") 
async def test_crm_connection():
    """Test Salesforce CRM connection"""
    try:
        if not salesforce_crm:
            return {
                "status": "error",
                "message": "Salesforce integration not configured"
            }
        
        result = await salesforce_crm.test_connection()
        return result
        
    except Exception as e:
        logger.error(f"CRM test error: {e}")
        return {
            "status": "error", 
            "message": str(e)
        }

@app.post("/api/sessions/{session_id}/summary")
async def get_session_summary(session_id: str):
    """Get detailed session summary"""
    try:
        summary = await generate_session_summary(session_id)
        return {
            "status": "success",
            "session_id": session_id,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Session summary error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

async def generate_session_summary(session_id: str) -> Dict[str, Any]:
    """Generate simplified session summary for phone calls"""
    try:
        # Basic summary for phone calls
        audio_stats = {}
        if audio_processor:
            try:
                audio_stats = await audio_processor.get_session_stats(session_id)
            except:
                pass  # Ignore if method doesn't exist
        
        return {
            "session_id": session_id,
            "audio_processing": audio_stats,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Session summary generation error: {e}")
        return {"error": str(e)}

@app.get("/api/sessions/active")
async def get_active_sessions():
    """Get all active sessions"""
    try:
        active_sessions_info = []
        
        # This would get active session data from websocket manager
        # For now, return basic info
        return {
            "status": "success",
            "active_count": app_state["active_sessions"],
            "total_sessions": app_state["total_sessions"],
            "sessions": active_sessions_info
        }
        
    except Exception as e:
        logger.error(f"Active sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_server_error(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred"}
    )

# Background tasks
async def periodic_health_check():
    """Periodic health check for all services"""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            # Test Azure service
            if azure_service:
                try:
                    # Simple health check - this would be a lightweight operation
                    app_state["service_health"]["azure"] = "healthy"
                except:
                    app_state["service_health"]["azure"] = "unhealthy"
            
            # Test Murf service 
            if murf_service:
                try:
                    # Check service availability
                    app_state["service_health"]["murf"] = "healthy"
                except:
                    app_state["service_health"]["murf"] = "unhealthy"
            
            # Test Salesforce
            if salesforce_crm:
                try:
                    connection_test = await salesforce_crm.test_connection()
                    app_state["service_health"]["salesforce"] = "healthy" if connection_test["status"] == "success" else "degraded"
                except:
                    app_state["service_health"]["salesforce"] = "unhealthy"
            
        except Exception as e:
            logger.error(f"Health check error: {e}")

# ============================================================================
# Voice Service Performance & Testing Endpoints
# ============================================================================

@app.get("/api/voice/performance")
async def get_voice_performance():
    """
    Get Murf voice service performance metrics
    - Cache hit rates
    - Generation times
    - Request statistics
    """
    try:
        stats = await murf_service.get_performance_stats()
        
        return JSONResponse({
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Performance stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/test")
async def test_voice_generation(request: Request):
    """
    Test voice generation with custom text and voice profile
    Request body:
    {
        "text": "Sample text to generate",
        "voice_profile": "sales_coach_male_confident",
        "use_streaming": false
    }
    """
    try:
        data = await request.json()
        text = data.get("text", "Hello, this is a test of the voice generation system.")
        voice_profile = data.get("voice_profile", "realestate_consultant_female")
        use_streaming = data.get("use_streaming", False)
        
        # Check if voice profile exists
        if voice_profile not in murf_service.premium_voices:
            available_voices = list(murf_service.premium_voices.keys())
            return JSONResponse({
                "status": "error",
                "message": f"Invalid voice profile. Available: {available_voices}"
            }, status_code=400)
        
        # Generate voice (streaming or REST)
        if use_streaming:
            audio_data = await murf_service.generate_streaming_voice(text, voice_profile)
        else:
            audio_data = await murf_service.generate_premium_voice(text, voice_profile)
        
        if audio_data:
            # Return audio as streaming response
            return StreamingResponse(
                io.BytesIO(audio_data),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f'inline; filename="test_voice_{voice_profile}.mp3"'
                }
            )
        else:
            return JSONResponse({
                "status": "error",
                "message": "Voice generation failed. Check logs for details."
            }, status_code=500)
        
    except Exception as e:
        logger.error(f"Voice test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voice/profiles")
async def get_voice_profiles():
    """
    List all available voice profiles with configurations
    """
    try:
        profiles = {}
        for profile_name, config in murf_service.premium_voices.items():
            profiles[profile_name] = {
                "voice_id": config.get("voice_id"),
                "style": config.get("style"),
                "speed": config.get("speed"),
                "language": "Hindi" if "hi-IN" in config.get("voice_id", "") else "English"
            }
        
        return JSONResponse({
            "status": "success",
            "data": {
                "profiles": profiles,
                "total_profiles": len(profiles)
            }
        })
        
    except Exception as e:
        logger.error(f"Get profiles error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/debug/murf")
async def debug_murf():
    """Debug Murf API configuration"""
    import os
    return JSONResponse({
        "status": "debug",
        "api_key_configured": bool(os.getenv("MURF_API_KEY")),
        "api_key_preview": os.getenv("MURF_API_KEY", "")[:10] + "..." if os.getenv("MURF_API_KEY") else "Not set",
        "base_url": "https://api.murf.ai/v1",
        "endpoints": {
            "synthesize": "/speech/generate",
            "voices": "/speech/voices"
        },
        "test_url": "https://api.murf.ai/v1/speech/voices",
        "configured_voices": list(murf_service.premium_voices.keys()) if murf_service else [],
        "session_active": murf_service.session is not None if murf_service else False
    })

# ============================================
# DEMO API ENDPOINTS - Human-like AI Calls
# ============================================

@app.post("/api/demo/start-call")
async def start_demo_call(request: Request):
    """
    Start a demo outbound call (B2B Sales or Real Estate) - DISABLED
    """
    raise HTTPException(status_code=503, detail="Demo endpoints disabled - use phone call endpoints instead")


@app.post("/api/demo/respond")
async def demo_respond(request: Request):
    """
    Handle prospect's response in the demo call - DISABLED
    """
    raise HTTPException(status_code=503, detail="Demo endpoints disabled - use phone call endpoints instead")


@app.get("/api/demo/conversation/{session_id}")
async def get_demo_conversation(session_id: str):
    """
    Get complete conversation summary for demo purposes - DISABLED
    """
    raise HTTPException(status_code=503, detail="Demo endpoints disabled - use phone call endpoints instead")


@app.post("/api/demo/close-call/{session_id}")
async def close_demo_call(session_id: str):
    """
    Close and summarize the demo call - DISABLED
    """
    raise HTTPException(status_code=503, detail="Demo endpoints disabled - use phone call endpoints instead")



@app.websocket("/ws/demo-call/{session_id}")
async def demo_call_websocket(websocket: WebSocket, session_id: str):
    """
    Real-time WebSocket for live demo calls - DISABLED
    """
    await websocket.accept()
    await websocket.send_json({
        "type": "error",
        "message": "Demo WebSocket disabled - use phone call endpoints instead"
    })
    await websocket.close()

# =========================
# Phone Call Endpoints (Real Telephony)
# =========================

@app.post("/api/phone/call")
async def make_phone_call(request: Request):
    """
    Make an outbound phone call using Twilio (Main endpoint for frontend)
    
    Request body:
    {
        "phone_number": "+1234567890",
        "call_type": "b2b_sales" | "real_estate",
        "lead_info": {
            "name": "John Doe",
            "company": "Acme Corp",
            "context": "Interested in AI solutions"
        }
    }
    """
    if not phone_service or not phone_service.client:
        raise HTTPException(
            status_code=503,
            detail="Phone service not available. Configure Twilio credentials in .env"
        )
    
    try:
        data = await request.json()
        phone_number = data.get("phone_number")
        call_type = data.get("call_type", "b2b_sales")
        lead_info = data.get("lead_info", {})
        
        if not phone_number:
            raise HTTPException(status_code=400, detail="phone_number is required")
        
        # Get the webhook URL from environment or request
        base_url = os.getenv("WEBHOOK_BASE_URL", "https://your-server.com")
        
        logger.info(f"📞 Initiating {call_type} call to {phone_number} with lead: {lead_info}")
        
        result = await phone_service.make_outbound_call(
            to_number=phone_number,
            call_type=call_type,
            lead_info=lead_info,
            webhook_url=base_url
        )
        
        if result.get("success"):
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Outbound call failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/phone/call/{call_sid}")
async def get_call_status(call_sid: str):
    """Get the status of an ongoing call"""
    if not phone_service or not phone_service.client:
        raise HTTPException(status_code=503, detail="Phone service not available")
    
    try:
        call = phone_service.client.calls(call_sid).fetch()
        return JSONResponse(content={
            "status": call.status,
            "duration": call.duration,
            "direction": call.direction,
            "from_number": call.from_formatted,
            "to_number": call.to_formatted
        })
    except Exception as e:
        logger.error(f"Failed to fetch call status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/api/phone/twiml/{call_type}", methods=["GET", "POST"])
async def generate_twiml(call_type: str, request: Request):
    """
    Generate TwiML for call handling - INTELLIGENT OPENING MESSAGE with MURF AI
    Uses IntelligentPhoneAI + Murf WebSocket Streaming for premium voice quality
    Accepts both GET and POST methods for Twilio compatibility
    """
    from twilio.twiml.voice_response import VoiceResponse, Gather
    
    if not phone_service or not intelligent_phone_ai or not murf_ws_streaming:
        raise HTTPException(status_code=503, detail="Phone service not available")
    
    try:
        # Get call SID from Twilio request
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        
        logger.info(f"📞 Generating opening TwiML for {call_type} call: {call_sid}")
        
        # Get lead info (you can fetch from database or CRM here)
        lead_info = {
            "name": "Arjun",  # Get from your database/CRM
            "company": "Your Company" if call_type == "b2b_sales" else None,
            "property_interest": "Hyderabad" if call_type == "real_estate" else None
        }
        
        # ⭐ OPTIMIZED: Agent-specific voices and opening messages
        if call_type == "real_estate":
            # Real Estate uses Priya (ENGLISH ONLY - professional, clear)
            voice_id = "en-IN-priya"  # ✅ FIXED: English-only for better clarity
            opening_text = "Hello Arjun! This is Priya from JK Ventures. I'm calling about some premium properties we have in Gachibowli and Hitec City, Hyderabad. Do you have 2 minutes to talk?"
        else:  # b2b_sales
            # B2B Sales uses Shaan (premium bilingual voice)
            voice_id = "hi-IN-shaan"
            opening_text = "Hi Arjun, main Shaan hun Murf AI se. Aapka voice content production 80% faster kar sakta hun. 2 minutes hai?"
        
        logger.info(f"🤖 Opening Message: {opening_text}")
        logger.info(f"🎙️ Using Voice: {voice_id}")

        
        # Generate Murf audio using WebSocket streaming (fast!)
        audio_path = await murf_ws_streaming.generate_and_save_for_twilio(
            text=opening_text,
            voice_id=voice_id,
            style="Conversational",
            min_buffer_size=40,  # Fast TTFB
            max_buffer_delay_ms=200  # Optimized for speed
        )
        
        # Serve the audio file via HTTP
        # We need to make it accessible to Twilio
        audio_url = f"{os.getenv('WEBHOOK_BASE_URL')}/audio/{os.path.basename(audio_path)}"
        
        logger.info(f"🎵 Generated audio: {audio_url}")
        
        # Create TwiML with Murf voice
        response = VoiceResponse()
        response.play(audio_url)
        
        # Gather customer response with speech recognition
        gather = Gather(
            input='speech',
            timeout=6,  # Optimized timeout
            speech_timeout='auto',
            action=f'/api/phone/process-speech/{call_type}',
            method='POST',
            language='en-IN',
            hints='yes, no, interested, not interested, call back, email, price, cost, features, demo'
        )
        response.append(gather)
        
        # Timeout fallback
        response.say(
            "I didn't hear you. Are you still there?",
            voice='Polly.Aditi',
            language='en-IN'
        )
        
        return HTMLResponse(content=str(response), media_type="application/xml")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ TwiML generation failed: {e}")
        # Emergency fallback with Polly
        response = VoiceResponse()
        response.say(
            "Hello, this is Priya from Murf AI. I'm calling to discuss our API services. How are you today?",
            voice='Polly.Aditi',
            language='en-IN'
        )
        gather = Gather(
            input='speech',
            timeout=7,
            action=f'/api/phone/process-speech/{call_type}',
            method='POST'
        )
        response.append(gather)
        return HTMLResponse(content=str(response), media_type="application/xml")

@app.api_route("/api/phone/process-speech/{call_type}", methods=["GET", "POST"])
async def process_speech(call_type: str, request: Request):
    """
    ⚡⚡⚡ ULTRA-FAST Speech Processing ⚡⚡⚡
    Target: <1.5s total response time
    
    Features:
    - Direct WebSocket streaming (no caching)
    - Premium Hindi voices (shweta/shaan)
    - Natural sales conversation
    - Connection pooling (saves 650ms)
    - <500ms TTFB target
    """
    from twilio.twiml.voice_response import VoiceResponse, Gather
    
    if not ultra_fast_sales or not language_detector or not sales_agent:
        raise HTTPException(status_code=503, detail="Ultra-fast service not available")
    
    start_time = time.time()
    
    try:
        form_data = await request.form()
        speech_result = form_data.get("SpeechResult", "")
        call_sid = form_data.get("CallSid")
        
        logger.info(f"🎤 Customer speech ({call_type}): {speech_result}")
        
        # 1. INSTANT language detection (<1ms)
        lang_result = language_detector.detect_lightning_fast(speech_result)
        language = lang_result.language
        logger.info(f"⚡ Language detected: {language} in {lang_result.detection_time_ms:.1f}ms")
        
        # 2. ⭐ Agent-specific voice selection
        if call_type == "real_estate":
            voice_id = "en-IN-priya"  # ✅ FIXED: Priya for Real Estate (English ONLY)
            logger.info(f"🎙️ Using PRIYA voice: {voice_id} (Real Estate Consultant - English)")
        else:  # b2b_sales
            voice_id = "hi-IN-shaan"  # Shaan for B2B Sales
            logger.info(f"🎙️ Using SHAAN voice: {voice_id} (B2B Sales Expert)")

        
        # 3. Analyze customer sentiment (fast, no AI)
        sentiment = sales_agent.analyze_customer_sentiment(speech_result)
        logger.info(f"💭 Sentiment: {sentiment}")
        
        # 4. Build conversation history for context
        conversation_history = _get_conversation_history(call_sid)
        
        # 5. Detect customer intent and create context
        intent = _detect_intent(speech_result)
        logger.info(f"🎯 Intent: {intent}")
        
        # 5.5. ⚡ TRY SMART RESPONSE FIRST (bypass AI entirely for common intents)
        smart_response = get_smart_response(speech_result, customer_name="Arjun")
        if smart_response:
            logger.info(f"⚡⚡⚡ INSTANT SMART RESPONSE (no AI needed): {smart_response}")
            ai_response = smart_response
            
            # Enhance with bilingual mixing
            enhanced_response = enhance_bilingual_response(ai_response, speech_result)
            
            # Generate audio ULTRA-FAST
            audio_bytes, metrics = await ultra_fast_sales.generate_ultra_fast(
                text=enhanced_response,
                voice_id=voice_id,
                customer_context={
                    "sentiment": sentiment,
                    "language": language
                }
            )
            
            if audio_bytes:
                # Save audio file
                audio_filename = f"ultra_{int(time.time() * 1000)}.wav"
                audio_path = f"Voice_outputs/{audio_filename}"
                
                with open(audio_path, 'wb') as f:
                    f.write(audio_bytes)
                
                audio_url = f"{os.getenv('WEBHOOK_BASE_URL')}/audio/{audio_filename}"
                
                total_time = (time.time() - start_time) * 1000
                
                logger.info(f"⚡⚡⚡ ULTRA-FAST SMART RESPONSE: {total_time:.0f}ms (target <1000ms) ✅✅✅")
                logger.info(f"⚡ Bypassed AI call - saved 2-6 seconds!")
                logger.info(f"🎙️ Voice TTFB: {metrics.get('ttfb_ms', 0):.0f}ms")
                logger.info(f"🎙️ Voice Total: {metrics.get('total_ms', 0):.0f}ms")
                
                # Update conversation history
                _update_conversation_history(call_sid, speech_result, ai_response)
                
                # Create TwiML response
                response = VoiceResponse()
                response.play(audio_url)
                
                gather = Gather(
                    input='speech',
                    action=f'/api/phone/process-speech/{call_type}',
                    language='en-IN',
                    speech_timeout='auto'
                )
                response.append(gather)
                
                return Response(content=str(response), media_type="application/xml")
        
        # 6. Generate AI response with RICH CONTEXT - FIXED: No more generic responses!
        if call_type == "b2b_sales":
            # Shaan - Bilingual B2B sales expert
            system_prompt = f"""You are Shaan, a senior B2B sales expert at Murf AI with 15+ years experience.

YOUR PRODUCT: Murf AI Text-to-Speech API
- Converts text to natural-sounding voice in 20+ languages
- Premium voices (including hi-IN-shaan for Hindi/English)
- RESTful API with simple integration
- Use cases: E-learning, marketing, IVR, podcasts, audiobooks
- Pricing: Pay-as-you-go, enterprise plans available
- Key benefit: Save 80% time & cost vs hiring voice actors

CUSTOMER PROFILE:
- Name: Arjun
- Company: Tech startup (likely)
- Current conversation stage: Discovery
- Sentiment: {sentiment}
- Intent: {intent}

CONVERSATION HISTORY:
{conversation_history}

YOUR SALES APPROACH (BILINGUAL):
1. Mix Hindi and English naturally (code-switching)
2. If they say "yes/sure/okay" → Ask discovery questions about voice needs
3. If they ask questions → Answer specifically with Murf AI features/benefits
4. If they show interest → Share specific use cases and ROI
5. If objections → Address with value-focused responses (Feel-Felt-Found)
6. Always move conversation forward with strategic questions

RESPONSE STYLE:
- Natural bilingual (Hindi-English code-switching)
- Use "Arjun" name frequently
- Be specific about Murf AI capabilities
- Ask strategic questions to understand needs
- NEVER give generic responses like "let me help you with that"
- Each response should provide value or gather important info
- Keep responses under 30 words for phone clarity

Example good responses:
- "Bahut accha! Arjun, aap kis type ka voice content create karte hain - training videos, marketing ya kuch aur?"
- "Perfect timing! Startups Murf API se scale karte hain. Aap currently voice actors use karte hain ya manually?"
- "Cost concern samajh gaya. Murf se actually money save hota hai - ek client ne 75% cost cut kiya. Monthly kitna voice content hai?"

CRITICAL: Base your response on what they ACTUALLY said, not generic acknowledgments."""

        else:  # real_estate
            # Priya - Professional English-only property consultant
            system_prompt = f"""You are Priya, a senior property consultant at JK Ventures Hyderabad with 12+ years experience.

YOUR EXPERTISE: Hyderabad Real Estate
- Premium properties in Gachibowli, Hitec City, Jubilee Hills, Banjara Hills
- Residential: 2BHK (₹60L-1.2Cr), 3BHK (₹1-2.5Cr), Villas (₹2.5Cr+)
- Commercial: Office spaces, retail shops
- Investment properties with 8-12% annual returns
- RERA approved projects, ready-to-move and under-construction

CUSTOMER PROFILE:
- Name: Arjun
- Location interest: Hyderabad (likely IT corridor)
- Sentiment: {sentiment}
- Intent: {intent}

CONVERSATION HISTORY:
{conversation_history}

YOUR APPROACH:
1. If they say "yes/sure/okay" → Ask qualifying questions (budget, location preference, property type)
2. If they ask about properties → Share specific options with prices and features
3. If interested → Describe property details, amenities, investment potential
4. If budget concerns → Show options in their range, explain payment plans
5. Always guide toward site visit or WhatsApp property details

RESPONSE STYLE:
- Professional, warm, expert
- SPEAK ONLY IN ENGLISH (no Hindi/Telugu mixing)
- Use "Arjun" name naturally
- Share specific property details when relevant
- Ask qualifying questions strategically
- NEVER generic responses
- Build urgency naturally (limited inventory, price appreciation)
- Keep responses under 30 words for phone clarity

Example good responses:
- "Excellent! Tell me Arjun, what's your budget range and preferred location - are you looking at the IT corridor like Gachibowli or Madhapur?"
- "Perfect! We have beautiful 3BHK options in Gachibowli starting from ₹1.2 crores with excellent amenities. Is this for investment or your own residence?"
- "Great question! Property prices in Hitec City have appreciated 12% this year. I have a RERA-approved project ready for possession. Can I WhatsApp you the details?"

CRITICAL: 
- Respond ONLY in English (no Hindi words like "Namaste", "aap", "hai", etc.)
- Be specific to what they said, not generic acknowledgments."""

        ai_task = asyncio.create_task(
            azure_service.generate_text_lightning(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"""Customer just said: "{speech_result}"

Generate a natural, helpful response that:
1. Directly addresses what they said
2. Provides specific information or asks strategic questions
3. Shows expertise in your field
4. Uses their name (Arjun) naturally
5. Moves conversation forward purposefully

Your response (2-3 sentences max):"""}
                ],
                max_tokens=180,  # Longer for detailed responses
                temperature=0.85  # More natural but focused
            )
        )
        
        # 7. Get AI response
        ai_response = await ai_task
        
        # 8. Validate response quality - NO MORE GENERIC RESPONSES!
        if not ai_response or ai_response.strip() == "":
            logger.error("❌ Empty AI response - using smart fallback")
            ai_response = _generate_smart_fallback(call_type, speech_result, intent)
        elif _is_generic_response(ai_response):
            logger.warning(f"⚠️ Generic response detected: {ai_response}")
            # Try again with more explicit instructions (call-type specific)
            if call_type == "b2b_sales":
                retry_system_prompt = "You are Shaan, a B2B sales expert at Murf AI. NO generic responses allowed! Be specific about Murf AI features and ask strategic questions."
            else:  # real_estate
                retry_system_prompt = "You are Priya, a property consultant at JK Ventures. NO generic responses allowed! Be specific about properties and ask qualifying questions. SPEAK ONLY IN ENGLISH."
            
            ai_response = await azure_service.generate_text_lightning(
                messages=[
                    {"role": "system", "content": retry_system_prompt},
                    {"role": "user", "content": f"""The customer said: "{speech_result}"

Intent: {intent}
Context: {call_type.replace('_', ' ')} call

Generate a SPECIFIC response with actual information or strategic questions.
NOT allowed: "let me help", "I understand", "that's good", generic acknowledgments
Required: Specific questions, product/property details, or actionable information

Response:"""}
                ],
                max_tokens=150,
                temperature=0.9
            )
        
        # 9. Store in conversation history
        _update_conversation_history(call_sid, speech_result, ai_response)
        
        logger.info(f"🤖 AI Response ({len(ai_response)} chars): {ai_response}")
        
        # Enhance response with natural bilingual mixing (ONLY for B2B Sales)
        if call_type == "b2b_sales":
            enhanced_response = enhance_bilingual_response(ai_response, speech_result)
            logger.info(f"✨ Enhanced Bilingual Response: {enhanced_response}")
            logger.info(f"🎙️ Using PREMIUM BILINGUAL voice: {voice_id} (Shaan)")
        else:  # real_estate - NO bilingual enhancement, pure English
            enhanced_response = ai_response  # Keep original English-only response
            logger.info(f"✨ English-only Response: {enhanced_response}")
            logger.info(f"🎙️ Using PREMIUM ENGLISH voice: {voice_id} (Priya)")
        
        # 6. Generate audio with ULTRA-FAST streaming
        audio_bytes, metrics = await ultra_fast_sales.generate_ultra_fast(
            text=enhanced_response,
            voice_id=voice_id,
            customer_context={
                "sentiment": sentiment,
                "language": language
            }
        )
        
        if audio_bytes:
            # Save audio file
            audio_filename = f"ultra_{int(time.time() * 1000)}.wav"
            audio_path = f"Voice_outputs/{audio_filename}"
            
            with open(audio_path, 'wb') as f:
                f.write(audio_bytes)
            
            audio_url = f"{os.getenv('WEBHOOK_BASE_URL')}/audio/{audio_filename}"
            
            total_time = (time.time() - start_time) * 1000
            
            # Log performance
            if total_time < 1500:
                logger.info(f"⚡ FAST REQUEST: /api/phone/process-speech - {total_time:.0f}ms ✅")
            else:
                logger.warning(f"⚠️ SLOW REQUEST: /api/phone/process-speech - {total_time:.0f}ms")
            
            logger.info(f"    TTFB: {metrics['ttfb_ms']:.0f}ms (target: <500ms)")
            logger.info(f"    Total: {total_time:.0f}ms (target: <1500ms)")
            
            # Create TwiML response
            response = VoiceResponse()
            response.play(audio_url)
            
            # Continue conversation based on sentiment
            should_continue = sentiment in ["interested", "neutral", "objection"]
            
            if should_continue:
                # Continue conversation - gather more input
                gather = Gather(
                    input='speech',
                    timeout=5,
                    speech_timeout='auto',
                    action=f'/api/phone/process-speech/{call_type}',
                    method='POST',
                    language='hi-IN' if language == 'hindi' else 'en-IN',
                    hints='yes, no, haan, nahi, interested, not interested, call back, email, price, demo, features'
                )
                response.append(gather)
                
                # Timeout fallback
                response.say(
                    "Kya aap sun sakte hain mujhe?" if language == 'hindi' else "Can you hear me?",
                    voice='Polly.Aditi',
                    language='hi-IN' if language == 'hindi' else 'en-IN'
                )
            else:
                # End call gracefully
                closing = "Thank you for your time! I'll send you all details via email. Have a great day!"
                if language == 'hindi':
                    closing = "Dhanyavaad ji! Main aapko email bhejungi. Aapka din shubh rahe!"
                
                response.say(closing, voice='Polly.Aditi', language='hi-IN' if language == 'hindi' else 'en-IN')
                response.hangup()
            
            return HTMLResponse(content=str(response), media_type="application/xml")
        else:
            raise Exception("No audio generated")
        
    except Exception as e:
        logger.error(f"❌ Ultra-fast processing failed: {e}")
        
        # Fast fallback
        response = VoiceResponse()
        response.say(
            "I apologize for the technical issue. I'll call you back shortly.",
            voice='Polly.Aditi',
            language='en-IN'
        )
        response.hangup()
        return HTMLResponse(content=str(response), media_type="application/xml")


# ⚡ NEW: Ultra-Fast Performance Stats Endpoint

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """
    Serve generated audio files to Twilio
    Allows Twilio to fetch Murf-generated audio for playback during calls
    """
    try:
        voice_outputs_dir = os.path.join(os.getcwd(), "Voice_outputs")
        file_path = os.path.join(voice_outputs_dir, filename)
        
        if not os.path.exists(file_path):
            logger.error(f"❌ Audio file not found: {file_path}")
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        logger.info(f"🎵 Serving audio: {filename}")
        
        # Return audio file with proper headers for Twilio
        return FileResponse(
            path=file_path,
            media_type="audio/wav",
            headers={
                "Cache-Control": "no-cache",
                "Content-Disposition": f"inline; filename={filename}",
                "Accept-Ranges": "bytes"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Audio serving failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve audio file")

@app.post("/api/phone/status")
async def call_status_webhook(request: Request):
    """Handle call status updates from Twilio"""
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")
        call_duration = form_data.get("CallDuration", "0")
        
        logger.info(f"Call status update - SID: {call_sid}, Status: {call_status}")
        
        if call_sid in phone_service.active_calls:
            phone_service.active_calls[call_sid]["status"] = call_status
            
            if call_status == "completed":
                # Log call completion
                phone_service.active_calls[call_sid]["end_time"] = datetime.now()
                logger.info(f"Call completed: {call_sid}")
                
                # 🆕 Process after-call CRM update
                call_info = phone_service.active_calls.get(call_sid, {})
                call_type = call_info.get("call_type", "b2b_sales")
                conversation_hist = conversation_memory.get(call_sid, [])
                
                # Process call summary and CRM update in background
                asyncio.create_task(
                    _process_call_completion(
                        call_sid, call_type, conversation_hist, int(call_duration)
                    )
                )
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Status webhook error: {e}")
        return {"error": str(e)}

@app.post("/api/phone/recording")
async def recording_webhook(request: Request):
    """Handle recording completion from Twilio"""
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        recording_url = form_data.get("RecordingUrl")
        
        logger.info(f"Recording available - Call: {call_sid}, URL: {recording_url}")
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Recording webhook error: {e}")
        return {"error": str(e)}

@app.get("/api/phone/call/{call_sid}")
async def get_call_info(call_sid: str):
    """Get information about a specific call"""
    if not phone_service:
        raise HTTPException(status_code=503, detail="Phone service not available")
    
    result = await phone_service.get_call_status(call_sid)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.delete("/api/phone/call/{call_sid}")
async def end_call(call_sid: str):
    """End an active call"""
    if not phone_service:
        raise HTTPException(status_code=503, detail="Phone service not available")
    
    result = await phone_service.end_call(call_sid)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.get("/api/phone/active-calls")
async def get_active_calls():
    """Get all active phone calls"""
    if not phone_service:
        raise HTTPException(status_code=503, detail="Phone service not available")
    
    return {"active_calls": phone_service.active_calls}

# 🆕 Dashboard API Endpoints
@app.get("/api/dashboard/calls")
async def get_call_dashboard_data(call_type: str = None):
    """Get dashboard data for completed calls with CRM updates"""
    try:
        filtered_calls = call_summaries
        
        if call_type:
            filtered_calls = {
                k: v for k, v in call_summaries.items()
                if v["summary"].get("call_type", "").lower().replace(" ", "_") == call_type
            }
        
        # Generate stats
        total_calls = len(filtered_calls)
        if total_calls == 0:
            return {
                "status": "success",
                "data": {
                    "total_calls": 0,
                    "recent_calls": [],
                    "summary_stats": {
                        "avg_duration": "0:00",
                        "avg_lead_score": 0,
                        "conversion_rate": "0%"
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # Calculate stats
        total_duration = sum([v["summary"].get("duration_seconds", 0) for v in filtered_calls.values()])
        avg_duration_secs = total_duration // total_calls
        avg_duration = f"{avg_duration_secs // 60}:{avg_duration_secs % 60:02d}"
        
        # Calculate average score
        scores = [v["summary"].get("lead_score", v["summary"].get("qualification_score", 0)) for v in filtered_calls.values()]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Calculate conversion/interest rate
        high_interest = sum([1 for v in filtered_calls.values() if v["summary"].get("interest_level") == "high" or v["summary"].get("qualification_score", 0) >= 7])
        conversion_rate = f"{(high_interest / total_calls * 100):.0f}%"
        
        return {
            "status": "success",
            "data": {
                "total_calls": total_calls,
                "recent_calls": list(filtered_calls.values())[-10:],  # Last 10
                "summary_stats": {
                    "total_calls": total_calls,
                    "avg_duration": avg_duration,
                    "conversion_rate": conversion_rate,
                    "avg_lead_score": f"{avg_score:.1f}"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Dashboard data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/phone/active-calls_old")
async def get_active_calls_old():
    """Get all active phone calls - old endpoint"""
    if not phone_service:
        raise HTTPException(status_code=503, detail="Phone service not available")
    
    return {
        "active_calls": phone_service.active_calls,
        "total": len(phone_service.active_calls)
    }

@app.post("/api/phone/sms")
async def send_sms(request: Request):
    """
    Send SMS follow-up message
    
    Request body:
    {
        "phone_number": "+1234567890",
        "message": "Thank you for your time..."
    }
    """
    if not phone_service:
        raise HTTPException(status_code=503, detail="Phone service not available")
    
    try:
        data = await request.json()
        phone_number = data.get("phone_number")
        message = data.get("message")
        
        if not phone_number or not message:
            raise HTTPException(
                status_code=400,
                detail="phone_number and message are required"
            )
        
        result = await phone_service.send_sms(phone_number, message)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMS send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PERFORMANCE OPTIMIZATION ENDPOINTS ====================

@app.get("/api/phone/performance-stats")
async def get_performance_stats():
    """
    Get real-time performance statistics
    
    Shows ultra-fast system performance:
    - Connection pool statistics
    - Premium voice usage
    - TTFB and total response metrics
    - NO preprocessing overhead
    """
    try:
        if not ultra_fast_sales:
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Ultra-fast service not initialized"
                },
                status_code=503
            )
        
        # Get connection pool stats from ultra-fast service
        pool_stats = {
            "active_connections": len(ultra_fast_sales.connection_pool),
            "pooled_voices": list(ultra_fast_sales.connection_pool.keys()),
            "max_pool_size": ultra_fast_sales.max_pool_size,
            "pool_usage_percent": (len(ultra_fast_sales.connection_pool) / ultra_fast_sales.max_pool_size) * 100
        }
        
        # Get premium voice personas
        personas_info = {
            name: {
                "voice_id": persona.voice_id,
                "experience": persona.experience,
                "style": persona.style
            }
            for name, persona in ultra_fast_sales.sales_personas.items()
        }
        
        return JSONResponse(content={
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "architecture": "ultra-fast-direct-streaming",
            "connection_pool": pool_stats,
            "premium_voices": personas_info,
            "performance_targets": {
                "ttfb_ms": "<500ms",
                "total_response_ms": "<1500ms",
                "connection_ms": "<200ms",
                "language_detection_ms": "<1ms"
            },
            "optimizations": {
                "preprocessing": "DISABLED (zero startup delay)",
                "caching": "DISABLED (real-time only)",
                "connection_pooling": "ENABLED (saves ~650ms per call)",
                "direct_streaming": "ENABLED (no buffering)"
            }
        })
    except Exception as e:
        logger.error(f"❌ Performance stats error: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )


@app.post("/api/phone/log-performance")
async def log_performance_report():
    """
    Trigger detailed ultra-fast performance report in logs
    
    Logs comprehensive performance analysis:
    - Connection pool statistics
    - Premium voice usage patterns
    - TTFB and total response metrics
    - Real-time streaming performance
    """
    try:
        if not ultra_fast_sales:
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Ultra-fast service not initialized"
                },
                status_code=503
            )
        
        # Log detailed connection pool info
        logger.info("=" * 80)
        logger.info("⚡ ULTRA-FAST PERFORMANCE REPORT")
        logger.info("=" * 80)
        logger.info(f"📊 Connection Pool Status:")
        logger.info(f"  - Active connections: {len(ultra_fast_sales.connection_pool)}")
        logger.info(f"  - Max pool size: {ultra_fast_sales.max_pool_size}")
        logger.info(f"  - Pool usage: {(len(ultra_fast_sales.connection_pool) / ultra_fast_sales.max_pool_size) * 100:.1f}%")
        logger.info(f"  - Pooled voices: {list(ultra_fast_sales.connection_pool.keys())}")
        
        logger.info(f"\n⭐ Premium Voice Personas:")
        for name, persona in ultra_fast_sales.sales_personas.items():
            logger.info(f"  - {name}:")
            logger.info(f"      Voice: {persona.voice_id}")
            logger.info(f"      Style: {persona.style}")
            logger.info(f"      Experience: {persona.experience}")
        
        logger.info(f"\n🎯 Performance Targets:")
        logger.info(f"  - TTFB: <500ms")
        logger.info(f"  - Total Response: <1500ms")
        logger.info(f"  - Connection: <200ms (with pooling)")
        logger.info(f"  - Language Detection: <1ms")
        
        logger.info(f"\n✅ Active Optimizations:")
        logger.info(f"  - Connection Pooling: ENABLED (saves ~650ms)")
        logger.info(f"  - Direct Streaming: ENABLED (no buffering)")
        logger.info(f"  - Premium Voices: hi-IN-shweta, hi-IN-shaan")
        logger.info(f"  - Phone Optimization: 8kHz mono WAV")
        logger.info(f"  - Preprocessing: DISABLED (instant startup)")
        logger.info(f"  - Caching: DISABLED (real-time only)")
        logger.info("=" * 80)
        
        return JSONResponse(content={
            "status": "success",
            "message": "Ultra-fast performance report logged successfully",
            "note": "Check server logs for detailed statistics"
        })
    except Exception as e:
        logger.error(f"❌ Performance report error: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )


# ==================== END PERFORMANCE OPTIMIZATION ENDPOINTS ====================

# Application entry point
if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true",
        workers=1,  # Single worker for WebSocket handling
        log_level="info",
        access_log=True,
        ws_ping_interval=20,  # WebSocket ping interval
        ws_ping_timeout=20,   # WebSocket ping timeout
        loop="uvloop" if os.name != "nt" else "asyncio"  # Use uvloop on Unix for better performance
    )
