import asyncio
import aiohttp
import json
import logging
import time
import base64
from typing import Dict, List, Any, Optional, Union
import os
from dotenv import load_dotenv

load_dotenv()

class MurfVoiceOptimized:
    """Direct Murf API implementation - Simple & Working"""
    
    def __init__(self):
        self.api_key = os.getenv("MURF_API_KEY")
        self.base_url = "https://api.murf.ai/v1"
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # ✅ CORRECT Murf API endpoints (from official docs)
        self.endpoints = {
            "synthesize": "/speech/generate",  # Main synthesis endpoint
            "voices": "/speech/voices",        # Get available voices
            "jobs": "/speech/jobs"             # Check job status (if async)
        }
        
        # ✅ VERIFIED voice IDs from Murf documentation
        self.premium_voices = {
            "realestate_consultant_female": {
                "voice_id": "en-IN-priya",
                "style": "conversational",
                "speed": 1.0,
                "pitch": 0
            },
            "realestate_consultant_male": {
                "voice_id": "en-IN-eashwar", 
                "style": "conversational",
                "speed": 0.95,
                "pitch": 0
            },
            "sales_coach_confident": {
                "voice_id": "en-IN-rohan",
                "style": "conversational",
                "speed": 1.1,
                "pitch": 0
            },
            "sales_coach_professional": {
                "voice_id": "en-IN-alia",
                "style": "narration", 
                "speed": 1.05,
                "pitch": 0
            },
            "hindi_agent_female": {
                "voice_id": "hi-IN-ayushi",
                "style": "conversational",
                "speed": 0.9,
                "pitch": 0
            },
            "hindi_agent_male": {
                "voice_id": "hi-IN-kabir",
                "style": "conversational",
                "speed": 0.85,
                "pitch": -1
            }
        }
        
        # Simple stats tracking
        self.stats = {
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "cache_hits": 0
        }
        
        # Audio cache
        self.audio_cache = {}

    async def initialize(self):
        """Initialize HTTP session with correct headers"""
        if not self.api_key:
            self.logger.warning("❌ MURF_API_KEY not found - voice synthesis disabled")
            return
            
        # ✅ CORRECT headers for Murf API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        timeout = aiohttp.ClientTimeout(total=30.0)
        connector = aiohttp.TCPConnector(limit=10, keepalive_timeout=30)
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
            connector=connector
        )
        
        self.logger.info("✅ Murf API session initialized")
        
        # Test the connection
        await self._test_connection()

    async def _test_connection(self):
        """Test Murf API connection by fetching available voices"""
        try:
            url = f"{self.base_url}{self.endpoints['voices']}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    voices_data = await response.json()
                    self.logger.info(f"✅ Murf API connected - {len(voices_data.get('voices', []))} voices available")
                else:
                    error_text = await response.text()
                    self.logger.error(f"❌ Murf API connection failed {response.status}: {error_text}")
        except Exception as e:
            self.logger.error(f"❌ Murf API connection test failed: {e}")
    
    async def _pregenerate_common_responses(self):
        """Pre-generate frequently used responses (best‑effort, non-fatal)."""
        phrases = {
            "sales_open": "Hi there, thanks for taking the time – I'd love to understand your current priority.",
            "sales_value": "Our customers typically see measurable ROI inside the very first quarter.",
            "re_welcome_en": "Hello! Happy to help you with property options today.",
            "re_budget_en": "What budget range are you considering so I can tailor the options?",
            "re_welcome_hi": "नमस्ते! मैं आपकी प्रॉपर्टी जरूरतों में मदद करने के लिए उपस्थित हूँ।"
        }
        
        # Log attempt
        self.logger.info(f"Attempting to pre-generate {len(phrases)} common phrases (best-effort)")
        
        tasks = []
        for key, text in phrases.items():
            if "hi" in key:
                profile = "hindi_property_agent_female"
            elif key.startswith("sales"):
                profile = "sales_coach_male_confident"
            else:
                profile = "realestate_consultant_female"
            tasks.append(self._generate_and_cache(key, text, profile))
        
        # Run with timeout and suppress errors (non-fatal)
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=10.0  # 10 second timeout for all pre-generations
            )
            successful = len([k for k in phrases.keys() if k in self.audio_cache])
            self.logger.info(f"Pre-generated {successful}/{len(phrases)} Murf phrases")
        except asyncio.TimeoutError:
            self.logger.warning("Pre-generation timed out - continuing without cache")
        except Exception as e:
            self.logger.warning(f"Pre-generation skipped: {e}")
    
    async def _generate_and_cache(self, key: str, text: str, profile: str):
        try:
            audio = await self.generate_premium_voice(text, profile)
            if audio:
                self.audio_cache[key] = {"audio": audio, "voice_profile": profile, "generated_at": time.time(), "text": text}
        except Exception as e:
            self.logger.debug(f"Cache warm skip {key}: {e}")
    
    async def generate_premium_voice(self, text: str, voice_profile: str = "realestate_consultant_female", custom_settings: Optional[Dict] = None) -> Optional[bytes]:
        """Generate voice via REST. Falls back gracefully on error."""
        if not self.api_key or not self.session:
            self.logger.warning("Cannot generate voice – missing API key/session")
            return None
        start = time.time()
        self.generation_stats["requests"] += 1
        self.generation_stats["total_characters"] += len(text)

        vcfg = self.premium_voices.get(voice_profile, next(iter(self.premium_voices.values())))
        if custom_settings:
            vcfg = {**vcfg, **custom_settings}

        cache_key = f"rest::{voice_profile}::{hash(text)}"
        cached = self.audio_cache.get(cache_key)
        if cached:
            self.generation_stats["cache_hits"] += 1
            return cached["audio"]

        payload = {
            "text": self._optimize_text_for_voice(text, vcfg),
            "voice_id": vcfg["voice_id"],
            "settings": {
                "style": vcfg.get("style", "Conversational"),
                "speed": vcfg.get("speed", 1.0),
                "pitch": vcfg.get("pitch", 0),
                "quality": "high",
                "format": "mp3",
                "sample_rate": 24000,
                "bitrate": 128
            }
        }
        try:
            url = f"{self.base_url}{self.REST_SYNTH_ENDPOINT}"
            self.logger.debug(f"Murf API request to: {url}")
            self.logger.debug(f"Payload keys: {list(payload.keys())}")
            
            async with self.session.post(url, json=payload) as resp:
                if resp.status == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        data = await resp.json()
                        # Murf returns audio_url that needs to be downloaded
                        audio_url = data.get("audio_url") or data.get("audioFile")
                        if audio_url:
                            # Download the actual audio file
                            async with self.session.get(audio_url) as audio_resp:
                                if audio_resp.status == 200:
                                    audio_bytes = await audio_resp.read()
                                else:
                                    self.logger.error(f"Failed to download audio from {audio_url}: {audio_resp.status}")
                                    return None
                        else:
                            # Fallback: check for base64 encoded audio
                            audio_b64 = data.get("audio") or data.get("audio_data")
                            if audio_b64:
                                audio_bytes = base64.b64decode(audio_b64)
                            else:
                                self.logger.error(f"JSON response missing audio_url or audio data: {data.keys()}")
                                return None
                    else:
                        # Direct binary audio response
                        audio_bytes = await resp.read()

                    self.audio_cache[cache_key] = {"audio": audio_bytes, "generated_at": time.time(), "voice_profile": voice_profile, "text": text}
                    self._update_avg_gen_time(time.time() - start)
                    return audio_bytes
                else:
                    err = await resp.text()
                    self.generation_stats["last_error"] = f"REST {resp.status}: {err[:120]}"
                    self.logger.error(f"Murf REST error {resp.status}: {err}")
        except Exception as e:
            self.generation_stats["last_error"] = str(e)
            self.logger.error(f"Murf REST exception: {e}")
        return None

    async def generate_streaming_voice(self, text: str, voice_profile: str = "realestate_consultant_female") -> Optional[bytes]:
        """Generate voice via WebSocket (buffer entire result, can be adapted to stream chunks)."""
        if not self.api_key:
            return None
        vcfg = self.premium_voices.get(voice_profile, next(iter(self.premium_voices.values())))
        request = {
            "voice_id": vcfg["voice_id"],
            "text": self._optimize_text_for_voice(text, vcfg),
            "format": self.websocket_config["format"],
            "sample_rate": self.websocket_config["sample_rate"],
            "advanced_settings": {
                "min_buffer_size": self.websocket_config["min_buffer_size"],
                "max_buffer_delay_ms": self.websocket_config["max_buffer_delay_ms"]
            },
            "voice_settings": {
                "style": vcfg.get("style", "Conversational"),
                "speed": vcfg.get("speed", 1.0),
                "pitch": vcfg.get("pitch", 0),
                "emphasis": vcfg.get("emphasis", "medium")
            }
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "api-key": self.api_key, "Content-Type": "application/json"}
        start = time.time()
        chunks: List[bytes] = []
        try:
            import websockets  # local import to avoid dependency issues if unused
            async with websockets.connect(self.WS_SYNTH_URL, extra_headers=headers, ping_timeout=20, ping_interval=20) as ws:
                await ws.send(json.dumps(request))
                async for msg in ws:
                    data = json.loads(msg)
                    dtype = data.get("type")
                    if dtype == "audio":
                        hex_chunk = data.get("data")
                        if hex_chunk:
                            try:
                                chunks.append(bytes.fromhex(hex_chunk))
                            except ValueError:
                                continue
                    elif dtype == "done":
                        break
                    elif dtype == "error":
                        self.generation_stats["last_error"] = data.get("message")
                        self.logger.error(f"Murf WS error: {data.get('message')}")
                        return None
        except Exception as e:
            self.generation_stats["last_error"] = str(e)
            self.logger.error(f"Murf WS exception: {e}")
            return None
        if chunks:
            self.generation_stats["websocket_generations"] += 1
            self._update_avg_gen_time(time.time() - start)
            return b"".join(chunks)
        return None
    
    def _optimize_text_for_voice(self, text: str, voice_config: Dict) -> str:
        # Lightweight naturalization (avoid over-markup to keep Murf compatibility)
        txt = text.strip()
        if not txt.endswith("."):
            txt += "."
        # Simple emphasis heuristics
        for kw in ["ROI", "value", "investment"]:
            if kw in txt:
                txt = txt.replace(kw, f"<emphasis level='moderate'>{kw}</emphasis>")
        return txt
    
    async def get_cached_response(self, key: str) -> Optional[bytes]:
        cached = self.audio_cache.get(key)
        if cached:
            self.generation_stats["cache_hits"] += 1
            return cached.get("audio") if isinstance(cached, dict) else cached
        return None
    
    async def generate_contextual_response(self, 
                                         response_context: Dict[str, Any],
                                         industry: str = "real_estate") -> Optional[bytes]:
        """Generate contextual response based on conversation analysis"""
        
        # Determine appropriate voice and response based on context
        if industry == "sales":
            return await self._generate_sales_response(response_context)
        elif industry == "real_estate":
            return await self._generate_realestate_response(response_context)
        
        return None
    
    async def _generate_sales_response(self, context: Dict[str, Any]) -> Optional[bytes]:
        """Generate sales-specific voice response"""
        
        response_type = context.get("response_type", "coaching")
        urgency = context.get("urgency", "medium")
        
        # Select voice based on urgency and context
        if urgency == "high":
            voice_profile = "sales_coach_male_confident"
        else:
            voice_profile = "sales_coach_female_professional"
        
        # Generate response text based on context
        if response_type == "objection_handling":
            text = context.get("objection_response", "Let me address that concern specifically.")
        elif response_type == "discovery":
            text = context.get("discovery_question", "Tell me more about your current challenges.")
        elif response_type == "value_proposition":
            text = context.get("value_statement", "Here's how this creates value for your business.")
        else:
            text = context.get("coaching_suggestion", "Continue building rapport and understanding their needs.")
        
        return await self.generate_premium_voice(text, voice_profile)
    
    async def _generate_realestate_response(self, context: Dict[str, Any]) -> Optional[bytes]:
        """Generate real estate specific voice response"""
        
        language = context.get("language", "english")
        response_type = context.get("response_type", "qualification")
        
        # Select appropriate voice
        if language == "hindi":
            voice_profile = "hindi_property_agent_female"
        else:
            voice_profile = "realestate_consultant_female"
        
        # Generate contextual response
        if response_type == "budget_inquiry":
            if language == "hindi":
                text = "आपका बजट क्या है इस प्रॉपर्टी के लिए?"
            else:
                text = "What budget range are you considering for this property?"
        elif response_type == "property_recommendation":
            property_name = context.get("property_name", "this excellent property")
            text = f"I'd like to tell you about {property_name}. It offers great value for your requirements."
        elif response_type == "site_visit":
            text = "Would you like to schedule a site visit to see the property in person?"
        else:
            text = context.get("response_text", "How can I help you with your property requirements?")
        
        return await self.generate_premium_voice(text, voice_profile)
    
    def _update_avg_gen_time(self, duration: float):
        total_ops = self.generation_stats["requests"] + self.generation_stats["websocket_generations"]
        if total_ops:
            prev = self.generation_stats["avg_generation_time"]
            self.generation_stats["avg_generation_time"] = (prev * (total_ops - 1) + duration) / total_ops

    async def get_performance_stats(self) -> Dict[str, Any]:
        cache_rate = (self.generation_stats["cache_hits"] / max(1, self.generation_stats["requests"])) * 100
        return {
            "requests_rest": self.generation_stats["requests"],
            "requests_ws": self.generation_stats["websocket_generations"],
            "cache_hits": self.generation_stats["cache_hits"],
            "cache_hit_rate": f"{cache_rate:.1f}%",
            "avg_generation_time_s": round(self.generation_stats["avg_generation_time"], 3),
            "total_characters": self.generation_stats["total_characters"],
            "voices_available": list(self.premium_voices.keys()),
            "last_error": self.generation_stats["last_error"]
        }
    
    async def close(self):
        if self.session:
            await self.session.close()
        ws = self.websocket
        if ws and hasattr(ws, "close"):
            try:
                maybe = ws.close()
                if asyncio.iscoroutine(maybe):
                    await maybe
            except Exception:
                pass
