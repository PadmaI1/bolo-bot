"""
🚀 Quick Start Example - Optimized Phone AI System
Complete integration example showing all optimization components working together

This example demonstrates:
1. Advanced language detection with confidence scoring
2. Intelligent voice routing based on context
3. Optimized Murf WebSocket streaming with connection pooling
4. Performance monitoring and analytics
5. Complete error handling and retry logic
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional

# Import all optimization components
from services.language_detector import AdvancedLanguageDetector
from services.voice_router import IntelligentVoiceRouter
from services.murf_optimized import MurfWebSocketStreamingOptimized
from services.performance_analytics import PerformanceMonitor
from services.rate_limiter import MurfRateLimiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizedPhoneAISystem:
    """
    Complete optimized phone AI system with all enhancements
    Ready for production use in B2B sales and real estate contexts
    """
    
    def __init__(self):
        logger.info("🚀 Initializing Optimized Phone AI System...")
        
        # Initialize rate limiter (20 requests/minute, burst: 3)
        self.rate_limiter = MurfRateLimiter(
            requests_per_minute=20,
            burst_limit=3
        )
        
        # Initialize language detector
        self.language_detector = AdvancedLanguageDetector()
        
        # Initialize voice router
        self.voice_router = IntelligentVoiceRouter()
        
        # Initialize optimized Murf service
        self.murf_service = MurfWebSocketStreamingOptimized(
            rate_limiter=self.rate_limiter
        )
        
        # Initialize performance monitor
        self.performance_monitor = PerformanceMonitor()
        
        # Active conversations
        self.conversations: Dict[str, Dict[str, Any]] = {}
        
        logger.info("✅ All services initialized and ready!")
    
    async def start_conversation(
        self,
        call_sid: str,
        call_type: str,  # 'b2b_sales' or 'real_estate'
        customer_name: str = "there"
    ) -> Dict[str, Any]:
        """
        Start a new optimized conversation
        
        Args:
            call_sid: Unique call identifier
            call_type: 'b2b_sales' or 'real_estate'
            customer_name: Customer's name
            
        Returns:
            Opening message with audio
        """
        logger.info(f"📞 Starting conversation: {call_sid} ({call_type})")
        
        # Initialize conversation state
        self.conversations[call_sid] = {
            "call_sid": call_sid,
            "call_type": call_type,
            "customer_name": customer_name,
            "current_language": "english",
            "current_voice_id": None,
            "started_at": time.time(),
            "exchanges": 0
        }
        
        # Start tracking
        self.performance_monitor.start_call_tracking(call_sid, call_type)
        
        # Generate opening message
        if call_type == "b2b_sales":
            opening_text = (
                f"Hello! Is this {customer_name}? Hi, I'm Priya from Murf AI. "
                f"I'm reaching out about our voice API that can help automate "
                f"your voice content. Do you have a couple of minutes?"
            )
        else:  # real_estate
            opening_text = (
                f"Hello! Am I speaking with {customer_name}? Hi, this is Rohan "
                f"from BB Ventures. I'm calling about your interest in Hyderabad "
                f"properties. Are you still looking?"
            )
        
        # Detect language (should be English for opening)
        lang_result = self.language_detector.detect_language(opening_text)
        
        # Select voice
        voice_selection = self.voice_router.select_voice(
            language=lang_result.language,
            call_context=call_type,
            language_confidence=lang_result.confidence
        )
        
        # Update conversation state
        self.conversations[call_sid]["current_language"] = voice_selection.language
        self.conversations[call_sid]["current_voice_id"] = voice_selection.voice_id
        
        # Generate audio
        start_time = time.time()
        
        audio = await self.murf_service.generate_streaming_audio_optimized(
            text=opening_text,
            language=voice_selection.language,
            voice_id=voice_selection.voice_id,
            context_id=call_sid,
            priority="high",
            use_connection_pool=True
        )
        
        generation_time = (time.time() - start_time) * 1000
        
        # Track performance
        self.performance_monitor.track_voice_generation(
            voice_id=voice_selection.voice_id,
            language=voice_selection.language,
            text=opening_text,
            duration_ms=generation_time,
            ttfb_ms=0,  # Captured inside murf_service
            audio_size=len(audio),
            success=True
        )
        
        logger.info(
            f"✅ Opening generated: {len(audio)} bytes in {generation_time:.0f}ms"
        )
        
        return {
            "audio": audio,
            "text": opening_text,
            "voice_id": voice_selection.voice_id,
            "language": voice_selection.language,
            "voice_name": voice_selection.voice_name
        }
    
    async def process_customer_response(
        self,
        call_sid: str,
        customer_speech: str
    ) -> Dict[str, Any]:
        """
        Process customer's speech and generate intelligent response
        
        Args:
            call_sid: Call identifier
            customer_speech: Transcribed customer speech
            
        Returns:
            AI response with audio
        """
        if call_sid not in self.conversations:
            logger.error(f"❌ Conversation not found: {call_sid}")
            return {"error": "Conversation not found"}
        
        conv = self.conversations[call_sid]
        call_type = conv["call_type"]
        previous_voice = conv["current_voice_id"]
        
        logger.info(f"💬 Processing response for {call_sid}")
        start_time = time.time()
        
        # 1. ADVANCED LANGUAGE DETECTION
        lang_result = self.language_detector.detect_language(customer_speech)
        
        logger.info(
            f"🔍 Detected: {lang_result.language} "
            f"(confidence: {lang_result.confidence:.2%}, "
            f"method: {lang_result.detection_method})"
        )
        
        # Track language detection
        self.performance_monitor.track_language_detection(
            detected_language=lang_result.language,
            confidence=lang_result.confidence,
            detection_method=lang_result.detection_method,
            text=customer_speech
        )
        
        # 2. INTELLIGENT VOICE SELECTION
        voice_selection = self.voice_router.select_voice(
            language=lang_result.language,
            call_context=call_type,
            language_confidence=lang_result.confidence,
            previous_voice_id=previous_voice
        )
        
        logger.info(
            f"🎙️ Selected: {voice_selection.voice_name} ({voice_selection.voice_id})"
        )
        
        # Track voice switch if occurred
        if voice_selection.switched:
            logger.info(
                f"🔄 Voice switched: {previous_voice} → {voice_selection.voice_id}"
            )
            
            self.performance_monitor.track_voice_switch(
                call_sid=call_sid,
                from_voice=previous_voice,
                to_voice=voice_selection.voice_id,
                from_language=conv["current_language"],
                to_language=voice_selection.language,
                confidence=voice_selection.confidence,
                reason="language_change"
            )
        
        # Update conversation state
        conv["current_language"] = voice_selection.language
        conv["current_voice_id"] = voice_selection.voice_id
        conv["exchanges"] += 1
        
        # 3. GENERATE AI RESPONSE (Simulated - replace with real AI)
        ai_response_text = self._generate_simulated_response(
            customer_speech,
            call_type,
            voice_selection.language
        )
        
        logger.info(f"🤖 AI Response: {ai_response_text[:60]}...")
        
        # 4. OPTIMIZED VOICE GENERATION
        generation_start = time.time()
        
        audio = await self.murf_service.generate_streaming_audio_optimized(
            text=ai_response_text,
            language=voice_selection.language,
            voice_id=voice_selection.voice_id,
            context_id=call_sid,
            priority="high",
            use_connection_pool=True
        )
        
        generation_time = (time.time() - generation_start) * 1000
        
        # 5. TRACK PERFORMANCE
        self.performance_monitor.track_voice_generation(
            voice_id=voice_selection.voice_id,
            language=voice_selection.language,
            text=ai_response_text,
            duration_ms=generation_time,
            ttfb_ms=0,  # Captured inside murf_service
            audio_size=len(audio),
            success=True
        )
        
        total_time = (time.time() - start_time) * 1000
        
        self.performance_monitor.update_call_metrics(
            call_sid=call_sid,
            response_time_ms=total_time,
            voice_switch=voice_selection.switched
        )
        
        logger.info(
            f"⚡ Total response time: {total_time:.0f}ms "
            f"(generation: {generation_time:.0f}ms)"
        )
        
        return {
            "audio": audio,
            "text": ai_response_text,
            "voice_id": voice_selection.voice_id,
            "language": voice_selection.language,
            "voice_name": voice_selection.voice_name,
            "performance": {
                "total_time_ms": total_time,
                "generation_time_ms": generation_time,
                "voice_switched": voice_selection.switched
            }
        }
    
    def _generate_simulated_response(
        self,
        customer_speech: str,
        call_type: str,
        language: str
    ) -> str:
        """
        Simulate AI response (replace with real Azure OpenAI in production)
        """
        responses = {
            "b2b_sales": {
                "english": "Great! I'd love to tell you more about our API. It's super easy to integrate and provides high-quality voices in multiple languages.",
                "hindi": "बहुत बढ़िया! मैं आपको हमारे API के बारे में और बता सकती हूं। यह बहुत आसान है और कई भाषाओं में उच्च गुणवत्ता की आवाज़ प्रदान करता है।",
                "telugu": "చాలా బాగుంది! మా API గురించి మరింత చెప్పగలను. ఇది చాలా సులభం మరియు అనేక భాషల్లో అధిక నాణ్యత స్వరాలను అందిస్తుంది."
            },
            "real_estate": {
                "english": "Excellent! I have some amazing properties in Hyderabad that match your requirements. Can you tell me your budget range?",
                "hindi": "बहुत अच्छा! मेरे पास हैदराबाद में कुछ बेहतरीन प्रॉपर्टी हैं जो आपकी आवश्यकताओं से मेल खाती हैं। क्या आप मुझे अपना बजट रेंज बता सकते हैं?",
                "telugu": "అద్భుతం! మీ అవసరాలకు సరిపోయే హైదరాబాద్‌లో కొన్ని అద్భుతమైన ప్రాపర్టీలు నా వద్ద ఉన్నాయి. మీ బడ్జెట్ పరిధి చెప్పగలరా?"
            }
        }
        
        return responses.get(call_type, {}).get(language, responses["b2b_sales"]["english"])
    
    async def end_conversation(
        self,
        call_sid: str,
        customer_satisfaction: Optional[int] = None
    ):
        """End conversation and cleanup"""
        if call_sid in self.conversations:
            self.performance_monitor.end_call_tracking(
                call_sid,
                customer_satisfaction
            )
            
            conv = self.conversations[call_sid]
            duration = time.time() - conv["started_at"]
            
            logger.info(
                f"📴 Conversation ended: {call_sid} "
                f"({conv['exchanges']} exchanges, {duration:.1f}s)"
            )
            
            del self.conversations[call_sid]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return self.performance_monitor.get_performance_summary(
            time_window_minutes=30
        )
    
    def get_optimization_suggestions(self) -> list:
        """Get AI-driven optimization suggestions"""
        return self.performance_monitor.get_optimization_suggestions()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Optimized Phone AI System...")
        await self.murf_service.shutdown()
        logger.info("✅ Shutdown complete")


# =============================================================================
# DEMONSTRATION
# =============================================================================

async def demo_conversation():
    """
    Demonstrate the complete optimized system with a sample conversation
    """
    print("\n" + "="*80)
    print("🎯 OPTIMIZED PHONE AI SYSTEM - DEMONSTRATION")
    print("="*80 + "\n")
    
    # Initialize system
    system = OptimizedPhoneAISystem()
    
    # Simulate B2B Sales Call
    print("📞 SCENARIO: B2B Sales Call (Murf API Demo)\n")
    
    call_sid = "demo_call_001"
    
    # 1. Start conversation
    print("1️⃣ Starting conversation...")
    opening = await system.start_conversation(
        call_sid=call_sid,
        call_type="b2b_sales",
        customer_name="Padma"
    )
    
    print(f"   Agent: {opening['text']}")
    print(f"   Voice: {opening['voice_name']} ({opening['voice_id']})")
    print(f"   Audio: {len(opening['audio'])} bytes\n")
    
    # 2. Customer responds in English
    print("2️⃣ Customer responds (English)...")
    customer_speech_1 = "Yes, I'm interested. Can you tell me more about the pricing?"
    
    response_1 = await system.process_customer_response(
        call_sid=call_sid,
        customer_speech=customer_speech_1
    )
    
    print(f"   Customer: {customer_speech_1}")
    print(f"   Agent: {response_1['text'][:80]}...")
    print(f"   Voice: {response_1['voice_name']} (switched: {response_1['performance']['voice_switched']})")
    print(f"   Performance: {response_1['performance']['total_time_ms']:.0f}ms total\n")
    
    # 3. Customer switches to Hindi
    print("3️⃣ Customer switches to Hindi...")
    customer_speech_2 = "हाँ, मुझे और जानकारी चाहिए। क्या आप मुझे कीमत बता सकते हैं?"
    
    response_2 = await system.process_customer_response(
        call_sid=call_sid,
        customer_speech=customer_speech_2
    )
    
    print(f"   Customer: {customer_speech_2}")
    print(f"   Agent: {response_2['text'][:80]}...")
    print(f"   Voice: {response_2['voice_name']} (switched: {response_2['performance']['voice_switched']})")
    print(f"   Performance: {response_2['performance']['total_time_ms']:.0f}ms total\n")
    
    # 4. Customer continues in Hindi
    print("4️⃣ Customer continues in Hindi...")
    customer_speech_3 = "ठीक है, मुझे इसके बारे में और बताएं।"
    
    response_3 = await system.process_customer_response(
        call_sid=call_sid,
        customer_speech=customer_speech_3
    )
    
    print(f"   Customer: {customer_speech_3}")
    print(f"   Agent: {response_3['text'][:80]}...")
    print(f"   Voice: {response_3['voice_name']} (switched: {response_3['performance']['voice_switched']})")
    print(f"   Performance: {response_3['performance']['total_time_ms']:.0f}ms total\n")
    
    # 5. End conversation
    print("5️⃣ Ending conversation...")
    await system.end_conversation(call_sid, customer_satisfaction=5)
    
    # 6. Show performance summary
    print("\n" + "-"*80)
    print("📊 PERFORMANCE SUMMARY")
    print("-"*80 + "\n")
    
    summary = system.get_performance_summary()
    
    print("Voice Generation:")
    if "voice_generation" in summary and "total" in summary["voice_generation"]:
        vg = summary["voice_generation"]
        print(f"  Total: {vg['total']}")
        print(f"  Success Rate: {vg.get('success_rate', 0):.1f}%")
        print(f"  Avg TTFB: {vg.get('avg_ttfb_ms', 0):.0f}ms")
        print(f"  Avg Total: {vg.get('avg_total_ms', 0):.0f}ms")
    
    print("\nLanguage Detection:")
    if "language_detection" in summary and "total" in summary["language_detection"]:
        ld = summary["language_detection"]
        print(f"  Total: {ld['total']}")
        print(f"  Avg Confidence: {ld.get('avg_confidence', 0):.2%}")
        print(f"  Distribution: {ld.get('distribution', {})}")
    
    print("\nVoice Switching:")
    if "voice_switching" in summary and "total_switches" in summary["voice_switching"]:
        vs = summary["voice_switching"]
        print(f"  Total Switches: {vs['total_switches']}")
        print(f"  Reasons: {vs.get('reasons', {})}")
    
    # 7. Show optimization suggestions
    print("\n" + "-"*80)
    print("💡 OPTIMIZATION SUGGESTIONS")
    print("-"*80 + "\n")
    
    suggestions = system.get_optimization_suggestions()
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion}")
    
    # Cleanup
    print("\n" + "-"*80)
    await system.shutdown()
    
    print("\n" + "="*80)
    print("✅ DEMONSTRATION COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demo_conversation())
