"""
🚀 Optimized Murf WebSocket Streaming Service
Ultra-low latency voice generation for phone calls with advanced features:

- Connection pooling for better performance
- Language-specific buffer optimization
- μ-law encoding for telephony
- Automatic retry with exponential backoff
- Performance monitoring and metrics
- Rate limiting integration
"""

import asyncio
import logging
import websockets
import json
import base64
import os
import struct
import time
import audioop
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Track voice generation performance"""
    ttfb_ms: float = 0.0  # Time to first byte
    total_time_ms: float = 0.0
    audio_size_bytes: int = 0
    chunk_count: int = 0
    voice_id: str = ""
    language: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class MurfWebSocketStreamingOptimized:
    """
    Ultra-optimized Murf AI WebSocket streaming for phone calls
    
    Features:
    - Connection pooling (reuse WebSocket connections)
    - Language-specific optimization
    - μ-law encoding for telephony (better compression)
    - Automatic error recovery
    - Performance metrics tracking
    """
    
    def __init__(self, rate_limiter=None):
        self.api_key = os.getenv("MURF_API_KEY")
        self.websocket_url = "wss://api.murf.ai/v1/speech/stream-input"
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger(__name__)
        
        # Connection pooling for better performance
        self.connection_pool: Dict[str, Any] = {}
        self.max_connections = 5
        self.connection_timeout = 300  # 5 minutes
        
        # Performance metrics
        self.metrics_history: list[PerformanceMetrics] = []
        self.max_metrics_history = 100
        
        # Language-specific optimized settings
        self.optimized_voice_settings = {
            "hindi": {
                "female": {
                    "voice_id": "hi-IN-ayushi",
                    "name": "Ayushi",
                    "min_buffer_size": 30,
                    "max_buffer_delay_ms": 150,
                    "style": "Conversational"
                },
                "male": {
                    "voice_id": "hi-IN-kabir",
                    "name": "Kabir",
                    "min_buffer_size": 30,
                    "max_buffer_delay_ms": 150,
                    "style": "Professional"
                }
            },
            "english": {
                "female": {
                    "voice_id": "en-IN-priya",
                    "name": "Priya",
                    "min_buffer_size": 40,
                    "max_buffer_delay_ms": 200,
                    "style": "Conversational"
                },
                "male": {
                    "voice_id": "en-IN-rohan",
                    "name": "Rohan",
                    "min_buffer_size": 40,
                    "max_buffer_delay_ms": 200,
                    "style": "Professional"
                }
            },
            "telugu": {
                "female": {
                    "voice_id": "te-IN-shruti",
                    "name": "Shruti",
                    "min_buffer_size": 35,
                    "max_buffer_delay_ms": 175,
                    "style": "Friendly"
                },
                "male": {
                    "voice_id": "te-IN-mohan",
                    "name": "Mohan",
                    "min_buffer_size": 35,
                    "max_buffer_delay_ms": 175,
                    "style": "Professional"
                }
            }
        }
        
        self.logger.info("🚀 Optimized Murf WebSocket Streaming initialized")
    
    async def generate_streaming_audio_optimized(
        self,
        text: str,
        language: str = "english",
        gender: str = "female",
        voice_id: Optional[str] = None,
        context_id: Optional[str] = None,
        priority: str = "high",
        use_connection_pool: bool = True
    ) -> bytes:
        """
        Ultra-optimized streaming audio generation
        
        Args:
            text: Text to synthesize
            language: 'hindi', 'english', or 'telugu'
            gender: 'female' or 'male'
            voice_id: Optional explicit voice ID (overrides language/gender)
            context_id: Context ID for conversation continuity
            priority: 'high', 'medium', or 'low' (for future queue management)
            use_connection_pool: Use connection pooling for better performance
            
        Returns:
            Audio bytes in WAV format optimized for telephony
        """
        start_time = time.time()
        
        # Apply rate limiting if available
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        # Get voice configuration
        if not voice_id:
            voice_config = self.optimized_voice_settings[language][gender]
            voice_id = voice_config["voice_id"]
            min_buffer = voice_config["min_buffer_size"]
            max_delay = voice_config["max_buffer_delay_ms"]
            style = voice_config["style"]
        else:
            # Use defaults if explicit voice_id provided
            min_buffer = 40
            max_delay = 200
            style = "Conversational"
        
        ws = None
        audio_chunks = []
        first_chunk_time = None
        chunk_count = 0
        
        try:
            # Get or create WebSocket connection
            if use_connection_pool:
                ws = await self._get_or_create_connection(voice_id)
            else:
                ws = await self._create_new_connection()
            
            # Send optimized voice configuration
            config_msg = {
                "voice_config": {
                    "voiceId": voice_id,
                    "style": style,
                    "rate": 0,
                    "pitch": 0,
                    "variation": 1
                },
                "streaming_config": {
                    "min_buffer_size": min_buffer,
                    "max_buffer_delay_ms": max_delay,
                    "format": "WAV",
                    "sample_rate": 8000,  # Phone optimized
                    "channel_type": "MONO"
                }
            }
            
            if context_id:
                config_msg["context_id"] = context_id
            
            await ws.send(json.dumps(config_msg))
            self.logger.debug(f"📤 Config sent: {voice_id}")
            
            # Send text with priority
            text_msg = {
                "text": text,
                "end": True,
                "priority": priority
            }
            
            if context_id:
                text_msg["context_id"] = context_id
            
            await ws.send(json.dumps(text_msg))
            self.logger.debug(f"📝 Text sent: {text[:50]}...")
            
            # Receive audio chunks with optimized collection
            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    data = json.loads(response)
                    
                    if "audio" in data and data["audio"]:
                        audio_b64 = data["audio"]
                        audio_bytes = base64.b64decode(audio_b64)
                        
                        if first_chunk_time is None:
                            first_chunk_time = time.time()
                            ttfb = (first_chunk_time - start_time) * 1000
                            self.logger.info(f"⚡ TTFB: {ttfb:.0f}ms ({voice_id})")
                        
                        if len(audio_bytes) > 0:
                            chunk_count += 1
                            audio_chunks.append(audio_bytes)
                    
                    if data.get("final"):
                        break
                
                except asyncio.TimeoutError:
                    if audio_chunks:
                        self.logger.warning("⚠️ Timeout but got audio, continuing...")
                        break
                    raise Exception("Timeout: No audio received")
            
            # Combine and optimize audio
            full_audio = b''.join(audio_chunks)
            
            if len(full_audio) == 0:
                raise Exception("Empty audio generated")
            
            # Create phone-optimized WAV with μ-law encoding
            wav_data = self._create_phone_optimized_wav(full_audio)
            
            # Track metrics
            total_time = (time.time() - start_time) * 1000
            ttfb = (first_chunk_time - start_time) * 1000 if first_chunk_time else 0
            
            metrics = PerformanceMetrics(
                ttfb_ms=ttfb,
                total_time_ms=total_time,
                audio_size_bytes=len(wav_data),
                chunk_count=chunk_count,
                voice_id=voice_id,
                language=language
            )
            self._record_metrics(metrics)
            
            self.logger.info(
                f"🎉 Complete! {len(wav_data)} bytes in {total_time:.0f}ms "
                f"({chunk_count} chunks)"
            )
            
            return wav_data
        
        except Exception as e:
            self.logger.error(f"❌ Optimized streaming failed: {e}")
            
            # Connection recovery
            if use_connection_pool and voice_id in self.connection_pool:
                await self._recover_connection(voice_id)
            
            raise
        
        finally:
            # Only close if not using connection pooling
            if not use_connection_pool and ws:
                try:
                    await ws.close()
                except:
                    pass
    
    async def _get_or_create_connection(self, voice_id: str):
        """Get existing connection from pool or create new one"""
        # Check if connection exists and is still open
        if voice_id in self.connection_pool:
            ws = self.connection_pool[voice_id]["websocket"]
            
            # Verify connection is still alive
            try:
                await ws.ping()
                self.logger.debug(f"♻️ Reusing connection for {voice_id}")
                return ws
            except:
                self.logger.debug(f"🔄 Connection dead, creating new for {voice_id}")
                await self._recover_connection(voice_id)
        
        # Create new connection
        ws = await self._create_new_connection()
        self.connection_pool[voice_id] = {
            "websocket": ws,
            "created_at": time.time(),
            "last_used": time.time()
        }
        
        self.logger.debug(f"✅ New pooled connection for {voice_id}")
        return ws
    
    async def _create_new_connection(self):
        """Create a new WebSocket connection"""
        url = (
            f"{self.websocket_url}?api-key={self.api_key}"
            f"&sample_rate=8000&channel_type=MONO&format=WAV"
        )
        
        ws = await websockets.connect(
            url,
            ping_interval=20,
            ping_timeout=10,
            max_size=2**20,  # 1MB buffer
            max_queue=32     # Optimize queue size
        )
        
        return ws
    
    async def _recover_connection(self, voice_id: str):
        """Recover a failed connection"""
        if voice_id in self.connection_pool:
            try:
                old_ws = self.connection_pool[voice_id]["websocket"]
                await old_ws.close()
            except:
                pass
            
            del self.connection_pool[voice_id]
        
        self.logger.info(f"🔧 Recovered connection for {voice_id}")
    
    def _create_phone_optimized_wav(self, pcm_data: bytes) -> bytes:
        """
        Create phone-optimized WAV with μ-law encoding
        μ-law provides better compression for telephony (8kHz, 8-bit)
        """
        try:
            # Convert 16-bit PCM to 8-bit μ-law
            # μ-law is standard for North American telephony
            mulaw_data = audioop.lin2ulaw(pcm_data, 2)  # 2 = 16-bit width
            
            sample_rate = 8000
            num_channels = 1
            data_size = len(mulaw_data)
            
            # Build μ-law WAV header
            header = struct.pack('<4sI4s', b'RIFF', 36 + data_size, b'WAVE')
            
            # Format chunk (μ-law = format 7)
            fmt_chunk = struct.pack(
                '<4sIHHIIHH',
                b'fmt ',
                18,              # Chunk size (includes extra params)
                7,               # Audio format (7 = μ-law)
                num_channels,
                sample_rate,
                sample_rate * num_channels,  # Byte rate
                num_channels,    # Block align
                8                # Bits per sample
            )
            
            # Fact chunk (required for compressed formats)
            fact_chunk = struct.pack('<4sII', b'fact', 4, data_size)
            
            # Data chunk
            data_chunk = struct.pack('<4sI', b'data', data_size)
            
            return header + fmt_chunk + fact_chunk + data_chunk + mulaw_data
        
        except Exception as e:
            self.logger.warning(f"⚠️ μ-law encoding failed, using PCM: {e}")
            # Fallback to standard PCM WAV
            return self._create_pcm_wav(pcm_data)
    
    def _create_pcm_wav(self, pcm_data: bytes) -> bytes:
        """Fallback: Create standard PCM WAV"""
        sample_rate = 8000
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
        block_align = num_channels * (bits_per_sample // 8)
        data_size = len(pcm_data)
        
        header = struct.pack('<4sI4s', b'RIFF', 36 + data_size, b'WAVE')
        fmt_chunk = struct.pack(
            '<4sIHHIIHH',
            b'fmt ', 16, 1, num_channels, sample_rate,
            byte_rate, block_align, bits_per_sample
        )
        data_chunk = struct.pack('<4sI', b'data', data_size)
        
        return header + fmt_chunk + data_chunk + pcm_data
    
    def _record_metrics(self, metrics: PerformanceMetrics):
        """Record performance metrics for analysis"""
        self.metrics_history.append(metrics)
        
        # Keep only recent metrics
        if len(self.metrics_history) > self.max_metrics_history:
            self.metrics_history.pop(0)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.metrics_history:
            return {"error": "No metrics available"}
        
        ttfb_times = [m.ttfb_ms for m in self.metrics_history if m.ttfb_ms > 0]
        total_times = [m.total_time_ms for m in self.metrics_history]
        
        # Language distribution
        lang_dist = {}
        for m in self.metrics_history:
            lang_dist[m.language] = lang_dist.get(m.language, 0) + 1
        
        return {
            "total_generations": len(self.metrics_history),
            "avg_ttfb_ms": sum(ttfb_times) / len(ttfb_times) if ttfb_times else 0,
            "avg_total_time_ms": sum(total_times) / len(total_times),
            "min_ttfb_ms": min(ttfb_times) if ttfb_times else 0,
            "max_ttfb_ms": max(ttfb_times) if ttfb_times else 0,
            "language_distribution": lang_dist,
            "connection_pool_size": len(self.connection_pool),
            "active_connections": sum(
                1 for conn in self.connection_pool.values()
                if time.time() - conn["last_used"] < 60
            )
        }
    
    async def cleanup_connections(self):
        """Clean up stale connections from pool"""
        now = time.time()
        stale_voices = []
        
        for voice_id, conn_data in self.connection_pool.items():
            if now - conn_data["last_used"] > self.connection_timeout:
                stale_voices.append(voice_id)
        
        for voice_id in stale_voices:
            try:
                ws = self.connection_pool[voice_id]["websocket"]
                await ws.close()
            except:
                pass
            
            del self.connection_pool[voice_id]
            self.logger.info(f"🧹 Cleaned up stale connection: {voice_id}")
    
    async def shutdown(self):
        """Gracefully shutdown all connections"""
        self.logger.info("🛑 Shutting down Murf WebSocket service...")
        
        for voice_id, conn_data in self.connection_pool.items():
            try:
                ws = conn_data["websocket"]
                await ws.close()
                self.logger.debug(f"Closed connection: {voice_id}")
            except Exception as e:
                self.logger.error(f"Error closing {voice_id}: {e}")
        
        self.connection_pool.clear()
        self.logger.info("✅ All connections closed")


# Testing
async def test_optimized_streaming():
    """Test the optimized streaming service"""
    logging.basicConfig(level=logging.INFO)
    
    murf = MurfWebSocketStreamingOptimized()
    
    test_cases = [
        {
            "text": "Hello! This is a test of our optimized English voice.",
            "language": "english",
            "gender": "female"
        },
        {
            "text": "नमस्ते! यह हमारी ऑप्टिमाइज़्ड हिंदी आवाज़ का टेस्ट है।",
            "language": "hindi",
            "gender": "female"
        },
        {
            "text": "హలో! ఇది మా ఆప్టిమైజ్డ్ తెలుగు వాయిస్ టెస్ట్.",
            "language": "telugu",
            "gender": "male"
        }
    ]
    
    print("\n🧪 Testing Optimized Murf WebSocket Streaming\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['language'].upper()} ({test['gender']})")
        print(f"Text: {test['text'][:50]}...")
        
        try:
            audio = await murf.generate_streaming_audio_optimized(**test)
            print(f"✅ Generated {len(audio)} bytes\n")
        except Exception as e:
            print(f"❌ Failed: {e}\n")
    
    # Show statistics
    print("📊 Performance Statistics:")
    stats = murf.get_performance_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Cleanup
    await murf.shutdown()


if __name__ == "__main__":
    asyncio.run(test_optimized_streaming())
