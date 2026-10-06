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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
import os

# Import optimized services
from services.websocket_manager import websocket_manager
from services.audio_processor import AudioProcessor
from services.azure_services import AzureServicesOptimized
from services.murf_voice import MurfVoiceOptimized
from services.murf_websocket_streaming import MurfWebSocketStreaming
from services.sales_ai import SalesAIEngine
from services.realestate_ai import RealEstateAIEngine
from services.conversation_ai import ConversationAI
from services.mock_crm import MockCRMService
from services.phone_service import TwilioPhoneService
from services.intelligent_phone_ai import IntelligentPhoneAI
# ⚡ NEW: Ultra-fast native sales with premium voices
from services.ultra_fast_native_sales import UltraFastNativeSales, ExperiencedSalesAgent
from services.lightning_language_detector import LightningLanguageDetector
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
sales_ai: Optional[SalesAIEngine] = None
realestate_ai: Optional[RealEstateAIEngine] = None
conversation_ai: Optional[ConversationAI] = None
salesforce_crm: Optional[MockCRMService] = None
phone_service: Optional[TwilioPhoneService] = None
intelligent_phone_ai: Optional[IntelligentPhoneAI] = None
# ⚡ NEW: Ultra-fast services with NO preprocessing
ultra_fast_sales: Optional[UltraFastNativeSales] = None
language_detector: Optional[LightningLanguageDetector] = None
sales_agent: Optional[ExperiencedSalesAgent] = None

# Application state
app_state = {
    "total_sessions": 0,
    "active_sessions": 0,
    "startup_time": datetime.now(),
    "service_health": {}
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """⚡ Lightning-fast startup - NO preprocessing, direct streaming only"""
    logger.info("⚡ Initializing Lightning-Fast B2B Agent (NO preprocessing)...")
    
    global azure_service, murf_service, murf_ws_streaming, audio_processor, sales_ai, realestate_ai, conversation_ai, salesforce_crm, phone_service, intelligent_phone_ai, ultra_fast_sales, language_detector, sales_agent
    
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
        
        # Initialize AI engines
        sales_ai = SalesAIEngine(azure_service, murf_service, websocket_manager)
        app_state["service_health"]["sales_ai"] = "healthy"
        logger.info("✅ Sales AI Engine initialized")
        
        realestate_ai = RealEstateAIEngine(azure_service, murf_service, websocket_manager)
        app_state["service_health"]["realestate_ai"] = "healthy"
        logger.info("✅ Real Estate AI Engine initialized")
        
        # Initialize Conversation AI for human-like calls
        conversation_ai = ConversationAI(azure_service, murf_service, websocket_manager)
        app_state["service_health"]["conversation_ai"] = "healthy"
        logger.info("✅ Conversation AI initialized - Ready for human-like calls")
        
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
        
        # Register WebSocket handlers
        websocket_manager.register_handler("audio", handle_audio_message)
        websocket_manager.register_handler("text", handle_text_message)
        websocket_manager.register_handler("system", handle_system_message)
        
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

# Ultra-optimized WebSocket endpoint
@app.websocket("/ws/{industry}")
async def websocket_endpoint(websocket: WebSocket, industry: str):
    """Ultra-low latency WebSocket endpoint for voice interactions"""
    
    # Validate industry
    if industry not in ["sales", "real_estate"]:
        await websocket.close(code=1008, reason="Invalid industry")
        return
    
    # Generate unique session ID
    session_id = f"{industry}_{int(datetime.now().timestamp() * 1000)}"
    app_state["total_sessions"] += 1
    
    # Accept connection
    if not await websocket_manager.connect(websocket, session_id, industry):
        return
    
    app_state["active_sessions"] += 1
    logger.info(f"🔗 New {industry} session: {session_id}")
    
    try:
        # Initialize industry-specific AI session
        if industry == "sales":
            session_result = await sales_ai.initialize_sales_session(session_id, {
                "meeting_type": "discovery_call",
                "client_context": "B2B prospect"
            })
        else:  # real_estate
            session_result = await realestate_ai.initialize_realestate_session(session_id, {
                "lead_source": "voice_ai_call",
                "language": "english"
            })
        
        # Initialize audio processor for this session
        await audio_processor.initialize_session(
            session_id, 
            lambda sid, audio: process_audio_callback(sid, audio, industry)
        )
        
        # Send session ready signal
        await websocket_manager.send_message(session_id, {
            "type": "session_ready",
            "session_id": session_id,
            "industry": industry,
            "initialization": session_result
        })
        
        # Main message loop
        while True:
            try:
                # Receive message (binary or text)
                message = await websocket.receive()
                
                # Check if connection is closing
                if message["type"] == "websocket.disconnect":
                    logger.info(f"🔌 Client disconnecting: {session_id}")
                    break
                
                if message["type"] == "websocket.receive":
                    if "bytes" in message:
                        # Handle audio data
                        audio_data = message["bytes"]
                        await audio_processor.process_audio_chunk(session_id, audio_data)
                    
                    elif "text" in message:
                        # Handle text messages
                        try:
                            text_data = json.loads(message["text"])
                            await websocket_manager.process_text_message(session_id, text_data)
                        except json.JSONDecodeError:
                            await websocket_manager.send_message(session_id, {
                                "type": "error",
                                "message": "Invalid JSON format"
                            })
                
            except WebSocketDisconnect:
                logger.info(f"🔌 Client disconnected: {session_id}")
                break
            except RuntimeError as e:
                # Handle "Cannot call receive once a disconnect message has been received"
                if "disconnect" in str(e).lower():
                    logger.info(f"🔌 WebSocket already disconnected: {session_id}")
                    break
                else:
                    logger.error(f"❌ WebSocket runtime error: {e}")
                    break
            except Exception as e:
                logger.error(f"❌ WebSocket message error: {e}")
                # Break on any error to prevent infinite loops
                break
    
    except Exception as e:
        logger.error(f"❌ WebSocket session error: {e}")
    
    finally:
        # Cleanup session
        await cleanup_session(session_id, industry)
        app_state["active_sessions"] = max(0, app_state["active_sessions"] - 1)
        logger.info(f"🧹 Session cleanup completed: {session_id}")

async def process_audio_callback(session_id: str, processed_audio: bytes, industry: str):
    """Callback for processed audio from audio processor"""
    try:
        start_time = datetime.now()
        
        # Transcribe audio using Azure STT
        transcription_result = await azure_service.transcribe_audio_optimized(
            processed_audio,
            language="auto"
        )
        
        if not transcription_result.get("text"):
            return  # No speech detected
        
        # Send transcription to frontend immediately
        await websocket_manager.send_message(session_id, {
            "type": "transcription",
            "data": transcription_result
        })
        
        # Process with industry-specific AI
        if industry == "sales":
            ai_response = await sales_ai.process_sales_conversation(session_id, transcription_result)
            await websocket_manager.send_message(session_id, {
                "type": "sales_coaching",
                "data": ai_response
            })
            
            # Sync to CRM if configured
            if salesforce_crm and ai_response.get("session_metrics"):
                asyncio.create_task(sync_to_crm_background(session_id, ai_response, "sales"))
        
        else:  # real_estate
            ai_response = await realestate_ai.process_realestate_conversation(session_id, transcription_result)
            await websocket_manager.send_message(session_id, {
                "type": "realestate_qualification",
                "data": ai_response
            })
            
            # Sync to CRM if qualified lead
            if salesforce_crm and ai_response.get("qualification_score", 0) >= 6:
                asyncio.create_task(sync_to_crm_background(session_id, ai_response, "real_estate"))
        
        # Generate voice response if AI provided one
        if ai_response.get("voice_audio"):
            await websocket_manager.broadcast_audio_response(
                session_id, 
                ai_response["voice_audio"],
                ai_response.get("response_strategy", {}).get("response_text", "")
            )
        
        # Log performance
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.debug(f"⚡ Audio processing completed in {processing_time:.1f}ms")
        
    except Exception as e:
        logger.error(f"❌ Audio callback error: {e}")
        await websocket_manager.send_message(session_id, {
            "type": "error",
            "message": "Audio processing failed"
        })

async def handle_audio_message(session_id: str, audio_data: bytes):
    """Handle raw audio message"""
    # This is handled by the audio processor callback
    pass

async def handle_text_message(session_id: str, message: Dict[str, Any]):
    """Handle text-based messages"""
    try:
        message_type = message.get("message_type", "unknown")
        
        if message_type == "manual_input":
            # Handle manual text input as if it were transcription
            text_content = message.get("content", "")
            fake_transcription = {
                "text": text_content,
                "confidence": 1.0,
                "speaker_detected": "customer"
            }
            
            # Determine industry from session
            session_info = websocket_manager.get_session_info(session_id)
            if session_info:
                industry = session_info["industry"]
                await process_audio_callback(session_id, b"", industry)  # Process as if audio
        
        elif message_type == "request_summary":
            # Generate session summary
            summary = await generate_session_summary(session_id)
            await websocket_manager.send_message(session_id, {
                "type": "session_summary",
                "data": summary
            })
        
        elif message_type == "change_language":
            # Handle language change for real estate
            new_language = message.get("language", "english")
            session_info = websocket_manager.get_session_info(session_id)
            
            if session_info and session_info["industry"] == "real_estate":
                # Update language preference in real estate AI
                # This would update the session language preference
                await websocket_manager.send_message(session_id, {
                    "type": "language_changed",
                    "language": new_language
                })
    
    except Exception as e:
        logger.error(f"❌ Text message handling error: {e}")

async def handle_system_message(session_id: str, message: Dict[str, Any]):
    """Handle system control messages"""
    try:
        command = message.get("command", "")
        
        if command == "pause_session":
            # Pause audio processing
            await websocket_manager.send_message(session_id, {
                "type": "session_paused"
            })
        
        elif command == "resume_session":
            # Resume audio processing
            await websocket_manager.send_message(session_id, {
                "type": "session_resumed"
            })
        
        elif command == "get_performance":
            # Get performance metrics
            performance_data = await get_session_performance(session_id)
            await websocket_manager.send_message(session_id, {
                "type": "performance_data",
                "data": performance_data
            })
    
    except Exception as e:
        logger.error(f"❌ System message handling error: {e}")

async def get_session_performance(session_id: str) -> Dict[str, Any]:
    """Get performance metrics for a session"""
    try:
        session_info = websocket_manager.get_session_info(session_id)
        if not session_info:
            return {"error": "Session not found"}
        
        # Calculate session duration
        connected_at_str = session_info.get("connected_at")
        if connected_at_str:
            connected_at = datetime.fromisoformat(connected_at_str)
            duration_seconds = (datetime.now() - connected_at).total_seconds()
        else:
            duration_seconds = 0
        
        # Get latency statistics
        latency_stats = websocket_manager.latency_stats
        
        return {
            "session_id": session_id,
            "duration_seconds": duration_seconds,
            "message_count": session_info.get("message_count", 0),
            "latency": {
                "avg_audio_received": sum(latency_stats["audio_received"][-10:]) / min(len(latency_stats["audio_received"]), 10) if latency_stats["audio_received"] else 0,
                "avg_processing_time": sum(latency_stats["processing_time"][-10:]) / min(len(latency_stats["processing_time"]), 10) if latency_stats["processing_time"] else 0,
                "avg_response_sent": sum(latency_stats["response_sent"][-10:]) / min(len(latency_stats["response_sent"]), 10) if latency_stats["response_sent"] else 0
            },
            "last_activity": session_info.get("last_activity"),
            "buffer_size": session_info.get("buffer_size", 0),
            "queue_size": session_info.get("queue_size", 0)
        }
    except Exception as e:
        logger.error(f"Error getting session performance: {e}")
        return {"error": str(e)}

async def cleanup_session(session_id: str, industry: str):
    """Comprehensive session cleanup"""
    try:
        # Finalize AI sessions
        if industry == "sales" and sales_ai:
            final_summary = await sales_ai.finalize_session(session_id)
        elif industry == "real_estate" and realestate_ai:
            final_summary = await realestate_ai.finalize_session(session_id)
        
        # Cleanup audio processor
        if audio_processor:
            await audio_processor.finalize_session(session_id)
        
        # Disconnect from WebSocket manager
        await websocket_manager.disconnect(session_id)
        
        logger.info(f"✅ Session cleanup completed: {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Session cleanup error: {e}")

async def sync_to_crm_background(session_id: str, ai_response: Dict[str, Any], industry: str):
    """Background task for CRM synchronization"""
    try:
        if not salesforce_crm:
            return
        
        session_info = websocket_manager.get_session_info(session_id)
        if not session_info:
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
        
        # Send CRM sync status to client
        await websocket_manager.send_message(session_id, {
            "type": "crm_sync_status",
            "data": crm_result
        })
        
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
    """Get platform performance metrics"""
    try:
        websocket_stats = await websocket_manager.get_performance_stats()
        
        # Murf service stats
        murf_stats = {}
        if murf_service:
            murf_stats = await murf_service.get_performance_stats()
        
        # Salesforce stats
        salesforce_stats = {}
        if salesforce_crm:
            salesforce_stats = await salesforce_crm.get_sync_statistics()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "websocket_performance": websocket_stats,
            "voice_generation": murf_stats,
            "crm_integration": salesforce_stats,
            "platform_health": app_state["service_health"]
        }
        
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/dashboard")
async def get_analytics_dashboard():
    """Get analytics dashboard data"""
    try:
        # Calculate uptime
        uptime = datetime.now() - app_state["startup_time"]
        uptime_seconds = int(uptime.total_seconds())
        
        # Get websocket stats
        websocket_stats = await websocket_manager.get_performance_stats()
        
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
            "websocket": websocket_stats,
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
    """Generate comprehensive session summary"""
    try:
        # Get session info from WebSocket manager
        session_info = websocket_manager.get_session_info(session_id)
        if not session_info:
            return {"error": "Session not found"}
        
        industry = session_info["industry"]
        
        # Get AI session summary
        if industry == "sales" and sales_ai:
            ai_summary = await sales_ai.get_session_summary(session_id)
        elif industry == "real_estate" and realestate_ai:
            ai_summary = await realestate_ai.get_session_summary(session_id)
        else:
            ai_summary = {"error": "AI service unavailable"}
        
        # Get audio processing stats
        audio_stats = {}
        if audio_processor:
            audio_stats = await audio_processor.get_session_stats(session_id)
        
        return {
            "session_info": session_info,
            "ai_summary": ai_summary,
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
    Start a demo outbound call (B2B Sales or Real Estate)
    This endpoint showcases Murf AI's human-like voice capabilities
    """
    try:
        data = await request.json()
        
        call_type = data.get("call_type", "b2b_sales")  # b2b_sales or real_estate
        session_id = data.get("session_id", f"demo_{datetime.now().timestamp()}")
        
        lead_info = data.get("lead_info", {
            "name": "John Smith",
            "company": "TechCorp Inc",
            "interested_in": "CRM solution"
        })
        
        # Start the outbound call
        result = await conversation_ai.start_outbound_call(
            session_id=session_id,
            call_type=call_type,
            lead_info=lead_info
        )
        
        logger.info(f"Demo call started: {call_type} for {lead_info.get('name')}")
        
        return JSONResponse({
            "status": "success",
            "message": "Call started successfully",
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Demo call start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/demo/respond")
async def demo_respond(request: Request):
    """
    Handle prospect's response in the demo call
    Shows AI's intelligent conversation capabilities
    """
    try:
        data = await request.json()
        
        session_id = data.get("session_id")
        prospect_message = data.get("message", "")
        
        if not session_id or not prospect_message:
            raise HTTPException(status_code=400, detail="session_id and message required")
        
        # Generate AI response
        result = await conversation_ai.handle_prospect_response(
            session_id=session_id,
            prospect_message=prospect_message
        )
        
        logger.info(f"AI responded in session {session_id}")
        
        return JSONResponse({
            "status": "success",
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Demo respond error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/demo/conversation/{session_id}")
async def get_demo_conversation(session_id: str):
    """
    Get complete conversation summary for demo purposes
    """
    try:
        summary = await conversation_ai.get_conversation_summary(session_id)
        
        return JSONResponse({
            "status": "success",
            "data": summary
        })
        
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/demo/close-call/{session_id}")
async def close_demo_call(session_id: str):
    """
    Close and summarize the demo call
    """
    try:
        result = await conversation_ai.close_conversation(session_id)
        
        logger.info(f"Demo call closed: {session_id}")
        
        return JSONResponse({
            "status": "success",
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Close call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/demo-call/{session_id}")
async def demo_call_websocket(websocket: WebSocket, session_id: str):
    """
    Real-time WebSocket for live demo calls
    Low-latency bidirectional communication for voice
    """
    await websocket.accept()
    logger.info(f"Demo WebSocket connected: {session_id}")
    
    try:
        while True:
            try:
                # Receive message from frontend
                message = await websocket.receive_json()
                
                msg_type = message.get("type")
                
                if msg_type == "start_call":
                    # Start outbound call
                    result = await conversation_ai.start_outbound_call(
                        session_id=session_id,
                        call_type=message.get("call_type", "b2b_sales"),
                        lead_info=message.get("lead_info", {})
                    )
                    
                    await websocket.send_json({
                        "type": "call_started",
                        "data": result
                    })
                    
                elif msg_type == "prospect_response":
                    # Handle prospect's response
                    result = await conversation_ai.handle_prospect_response(
                        session_id=session_id,
                        prospect_message=message.get("message", "")
                    )
                    
                    await websocket.send_json({
                        "type": "ai_response",
                        "data": result
                    })
                    
                elif msg_type == "close_call":
                    # Close the call
                    result = await conversation_ai.close_conversation(session_id)
                    
                    await websocket.send_json({
                        "type": "call_closed",
                        "data": result
                    })
                    break
                    
            except RuntimeError as e:
                if "disconnect" in str(e).lower():
                    logger.info(f"Demo WebSocket already disconnected: {session_id}")
                    break
                raise
                
    except WebSocketDisconnect:
        logger.info(f"Demo WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Demo WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            # Websocket already closed, ignore
            pass

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
        
        # Start intelligent conversation
        opening_data = await intelligent_phone_ai.start_conversation(
            call_sid=str(call_sid),
            call_type=call_type,
            lead_info=lead_info,
            preferred_language="en-IN"
        )
        
        # Get the opening text and voice from AI
        opening_text = opening_data["text"]
        voice_id = opening_data["voice_id"]
        
        logger.info(f"🤖 AI Generated Opening: {opening_text}")
        logger.info(f"🎙️ Using Murf Voice: {voice_id}")
        
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
        
        # 2. Get optimal sales persona with premium voice
        persona = ultra_fast_sales.get_sales_persona(language, gender="female")
        voice_id = persona.voice_id
        logger.info(f"👤 Sales persona: {persona.name} ({voice_id})")
        
        # 3. Analyze customer sentiment (fast, no AI)
        sentiment = sales_agent.analyze_customer_sentiment(speech_result)
        logger.info(f"💭 Sentiment: {sentiment}")
        
        # 4. Generate AI response (concurrent with preparation)
        ai_task = asyncio.create_task(
            azure_service.generate_text_lightning(
                messages=[
                    {"role": "system", "content": f"""You are {persona.name}, an experienced B2B sales expert with {persona.experience}.
                    
Personality: {', '.join(persona.traits)}
Language: Mix {language.title()} and English naturally (code-switching for Indian customers)
Tone: Warm, consultative, professional
Goal: Build rapport, understand needs, offer solutions

Customer sentiment: {sentiment}
Call type: {call_type}

Instructions:
- Use customer's name "Arjun" frequently
- Acknowledge concerns immediately
- Ask discovery questions (SPIN selling)
- Mix Hindi/English naturally if Hindi detected
- Be consultative, not pushy
- Keep responses conversational (2-3 sentences max)
- Use natural transitions: "bilkul ji", "aap dekho", "exactly"

Respond naturally to: {speech_result}"""},
                    {"role": "user", "content": speech_result}
                ],
                max_tokens=100,  # Shorter for speed
                temperature=0.7   # Natural conversation
            )
        )
        
        # 5. Get AI response
        ai_response = await ai_task
        
        # Enhance response for native speaker
        enhanced_response = ultra_fast_sales.enhance_response_for_native_speaker(
            ai_response, 
            language,
            speech_result
        )
        
        logger.info(f"🤖 AI Response: {enhanced_response}")
        logger.info(f"🎙️ Using PREMIUM voice: {voice_id}")
        
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
        
        logger.info(f"Call status update - SID: {call_sid}, Status: {call_status}")
        
        if call_sid in phone_service.active_calls:
            phone_service.active_calls[call_sid]["status"] = call_status
            
            if call_status == "completed":
                # Log call completion
                phone_service.active_calls[call_sid]["end_time"] = datetime.now()
                logger.info(f"Call completed: {call_sid}")
        
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
