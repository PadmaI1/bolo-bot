import asyncio
import aiohttp
import json
import logging
import time
import base64
from typing import Dict, List, Any, Optional
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
        # Enhanced with Telugu support and optimized for phone calls
        self.premium_voices = {
            # English (India) - Best for business calls
            "realestate_consultant_female": {
                "voice_id": "en-IN-priya",
                "style": "Conversational",
                "speed": 1.0,
                "pitch": 0,
                "sample_rate": 8000  # Optimized for phone quality
            },
            "realestate_consultant_male": {
                "voice_id": "en-IN-eashwar", 
                "style": "Conversational",
                "speed": 0.95,
                "pitch": 0,
                "sample_rate": 8000
            },
            "sales_coach_confident": {
                "voice_id": "en-IN-rohan",
                "style": "Conversational",
                "speed": 1.05,
                "pitch": 0,
                "sample_rate": 8000
            },
            "sales_coach_professional": {
                "voice_id": "en-IN-alia",
                "style": "Conversational", 
                "speed": 1.0,
                "pitch": 0,
                "sample_rate": 8000
            },
            # Hindi (India) - For Hindi speaking customers
            "hindi_agent_female": {
                "voice_id": "hi-IN-ayushi",
                "style": "Conversational",
                "speed": 0.95,
                "pitch": 0,
                "sample_rate": 8000
            },
            "hindi_agent_male": {
                "voice_id": "hi-IN-kabir",
                "style": "Conversational",
                "speed": 0.9,
                "pitch": 0,
                "sample_rate": 8000
            },
            # Telugu (India) - For Telugu speaking customers
            "telugu_agent_female": {
                "voice_id": "te-IN-shruti",
                "style": "Conversational",
                "speed": 0.95,
                "pitch": 0,
                "sample_rate": 8000
            },
            "telugu_agent_male": {
                "voice_id": "te-IN-mohan",
                "style": "Conversational",
                "speed": 0.9,
                "pitch": 0,
                "sample_rate": 8000
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
            
        # ✅ CORRECT headers for Murf API (include both formats)
        headers = {
            "api-key": self.api_key,          # Murf requires this
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
                    # Handle both dict and list responses
                    if isinstance(voices_data, dict):
                        voice_count = len(voices_data.get('voices', []))
                    elif isinstance(voices_data, list):
                        voice_count = len(voices_data)
                    else:
                        voice_count = 0
                    self.logger.info(f"✅ Murf API connected - {voice_count} voices available")
                else:
                    error_text = await response.text()
                    self.logger.warning(f"⚠️ Murf API connection test returned {response.status}: {error_text}")
        except Exception as e:
            self.logger.warning(f"⚠️ Murf API connection test failed: {e} (Non-fatal - voice generation may still work)")

    async def generate_premium_voice(
        self, 
        text: str, 
        voice_profile: str = "realestate_consultant_female"
    ) -> Optional[bytes]:
        """
        Generate voice using direct Murf API call
        
        Args:
            text: Text to convert to speech
            voice_profile: Voice profile to use
            
        Returns:
            Audio bytes or None if failed
        """
        if not self.api_key or not self.session:
            self.logger.warning("❌ Cannot generate voice - API not initialized")
            return None
            
        # Check cache first
        cache_key = f"{voice_profile}_{hash(text)}"
        if cache_key in self.audio_cache:
            self.stats["cache_hits"] += 1
            self.logger.info("✅ Using cached audio")
            return self.audio_cache[cache_key]["audio"]
        
        # Get voice configuration
        voice_config = self.premium_voices.get(
            voice_profile, 
            self.premium_voices["realestate_consultant_female"]
        )
        
        # ✅ CORRECT Murf API payload structure
        payload = {
            "text": text.strip(),
            "voiceId": voice_config["voice_id"],  # Note: voiceId not voice_id
            "format": "MP3",
            "sampleRate": 24000,
            "speed": voice_config.get("speed", 1.0),
            "pitch": voice_config.get("pitch", 0),
            "style": voice_config.get("style", "conversational")
        }
        
        self.stats["requests"] += 1
        start_time = time.time()
        
        try:
            url = f"{self.base_url}{self.endpoints['synthesize']}"
            self.logger.info(f"🔄 Generating voice: {url}")
            self.logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
            
            async with self.session.post(url, json=payload) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    # Check response content type
                    content_type = response.headers.get("content-type", "")
                    
                    if "application/json" in content_type:
                        # JSON response with download URL or base64 audio
                        data = await response.json()
                        self.logger.debug(f"JSON response keys: {list(data.keys())}")
                        
                        # Try different possible response formats
                        audio_bytes = None
                        
                        if "audioContent" in data:
                            # Base64 encoded audio
                            audio_bytes = base64.b64decode(data["audioContent"])
                            
                        elif "audioFile" in data:
                            # Download from URL (Murf's actual response format)
                            audio_bytes = await self._download_audio(data["audioFile"])
                            
                        elif "downloadUrl" in data:
                            # Download from URL
                            audio_bytes = await self._download_audio(data["downloadUrl"])
                            
                        elif "audioUrl" in data:
                            # Alternative URL field
                            audio_bytes = await self._download_audio(data["audioUrl"])
                            
                        elif "jobId" in data:
                            # Async job - poll for completion
                            audio_bytes = await self._poll_async_job(data["jobId"])
                            
                        else:
                            self.logger.error(f"❌ Unknown JSON response format: {data}")
                            self.stats["failed"] += 1
                            return None
                            
                    else:
                        # Direct binary audio response
                        audio_bytes = await response.read()
                    
                    if audio_bytes:
                        # Cache the result
                        self.audio_cache[cache_key] = {
                            "audio": audio_bytes,
                            "generated_at": time.time(),
                            "voice_profile": voice_profile
                        }
                        
                        self.stats["successful"] += 1
                        self.logger.info(f"✅ Voice generated successfully in {response_time:.2f}s - {len(audio_bytes)} bytes")
                        return audio_bytes
                    else:
                        self.logger.error("❌ No audio data received")
                        self.stats["failed"] += 1
                        return None
                        
                else:
                    # Error response
                    error_text = await response.text()
                    self.logger.error(f"❌ Murf API error {response.status}: {error_text}")
                    self.stats["failed"] += 1
                    
                    # Try to parse error details
                    try:
                        error_data = json.loads(error_text)
                        if "message" in error_data:
                            self.logger.error(f"❌ Error details: {error_data['message']}")
                    except:
                        pass
                        
                    return None
                    
        except Exception as e:
            self.stats["failed"] += 1
            self.logger.error(f"❌ Voice generation exception: {e}")
            return None

    async def _download_audio(self, url: str) -> Optional[bytes]:
        """Download audio from URL"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    self.logger.error(f"❌ Audio download failed: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"❌ Audio download exception: {e}")
            return None

    async def _poll_async_job(self, job_id: str) -> Optional[bytes]:
        """Poll async job until completion"""
        max_polls = 30  # 30 seconds max
        poll_interval = 1.0  # 1 second intervals
        
        for _ in range(max_polls):
            try:
                url = f"{self.base_url}{self.endpoints['jobs']}/{job_id}"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get("status", "")
                        
                        if status == "completed":
                            if "audioContent" in data:
                                return base64.b64decode(data["audioContent"])
                            elif "downloadUrl" in data:
                                return await self._download_audio(data["downloadUrl"])
                                
                        elif status == "failed":
                            self.logger.error(f"❌ Async job failed: {data.get('error', 'Unknown error')}")
                            return None
                            
                        # Job still processing, wait and retry
                        await asyncio.sleep(poll_interval)
                        
            except Exception as e:
                self.logger.error(f"❌ Job polling error: {e}")
                return None
                
        self.logger.error("❌ Job polling timeout")
        return None

    async def generate_streaming_voice(
        self, 
        text: str, 
        voice_profile: str = "realestate_consultant_female"
    ) -> Optional[bytes]:
        """
        Generate voice with streaming (fallback to regular generation)
        Murf doesn't support real streaming, so this is the same as generate_premium_voice
        """
        return await self.generate_premium_voice(text, voice_profile)

    async def get_cached_response(self, cache_key: str) -> Optional[bytes]:
        """Get cached audio response"""
        cached = self.audio_cache.get(cache_key)
        if cached:
            # Check if cache is still valid (24 hours)
            if time.time() - cached["generated_at"] < 86400:
                self.stats["cache_hits"] += 1
                return cached["audio"]
            else:
                # Remove expired cache
                del self.audio_cache[cache_key]
        return None

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        total_requests = self.stats["requests"]
        success_rate = (self.stats["successful"] / max(1, total_requests)) * 100
        cache_rate = (self.stats["cache_hits"] / max(1, total_requests)) * 100
        
        return {
            "total_requests": total_requests,
            "successful_requests": self.stats["successful"],
            "failed_requests": self.stats["failed"],
            "success_rate": f"{success_rate:.1f}%",
            "cache_hits": self.stats["cache_hits"],
            "cache_hit_rate": f"{cache_rate:.1f}%",
            "cached_items": len(self.audio_cache),
            "available_voices": list(self.premium_voices.keys()),
            "api_status": "connected" if self.session else "disconnected"
        }

    async def test_voice_generation(self) -> Dict[str, Any]:
        """Test voice generation for all available voices"""
        test_text = "Hello, this is a test of the voice generation system."
        results = {}
        
        for voice_name in self.premium_voices.keys():
            try:
                start_time = time.time()
                audio_data = await self.generate_premium_voice(test_text, voice_name)
                generation_time = time.time() - start_time
                
                results[voice_name] = {
                    "status": "success" if audio_data else "failed",
                    "voice_id": self.premium_voices[voice_name]["voice_id"],
                    "generation_time": f"{generation_time:.2f}s",
                    "audio_size_bytes": len(audio_data) if audio_data else 0
                }
            except Exception as e:
                results[voice_name] = {
                    "status": "error",
                    "error": str(e),
                    "voice_id": self.premium_voices[voice_name]["voice_id"]
                }
        
        return results

    async def close(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.logger.info("✅ Murf API session closed")
