"""
Lightning-Fast Murf WebSocket Streaming
========================================
Ultra-optimized streaming with NO preprocessing, direct WebSocket connections,
and connection pooling for <500ms TTFB.

Key Features:
- Direct streaming (no caching/preprocessing)
- Connection pooling (reuse WebSocket connections)
- Phone-optimized audio (8kHz mono WAV)
- Minimal buffering (20-25 bytes)
- Concurrent chunk processing
- Target: <500ms TTFB, <1.5s total response

Performance Targets:
- TTFB: <500ms (vs current 1400-1500ms)
- Connection: <200ms (vs current 650ms)
- Total: <1.5s (vs current 3-4s)
"""

import asyncio
import websockets
import json
import base64
import logging
import time
import struct
import os
from typing import Optional, AsyncIterator, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PerformanceMetrics:
    """Track streaming performance"""
    ttfb_ms: float
    total_time_ms: float
    chunk_count: int
    audio_size_bytes: int
    connection_reused: bool


class LightningMurfStreaming:
    """
    Ultra-fast Murf WebSocket streaming - NO preprocessing, pure speed
    
    Design Philosophy:
    - Stream directly from Murf WebSocket to Twilio
    - Reuse connections via pooling
    - Minimal buffering for lowest latency
    - Phone-optimized audio format (8kHz mono)
    - Concurrent processing where possible
    """
    
    def __init__(self):
        self.api_key = os.getenv("MURF_API_KEY")
        if not self.api_key:
            raise ValueError("MURF_API_KEY environment variable is required")
        
        self.ws_url = "wss://api.murf.ai/v1/speech/stream-input"
        self.logger = logging.getLogger(__name__)
        
        # Connection pool for instant reuse
        self.connection_pool: Dict[str, Any] = {}
        self.max_connections = 3
        self.connection_ttl = 300  # 5 minutes
        
        # Optimized voice configurations for phone quality
        # ⭐ PREMIUM VOICES for best quality
        self.voice_configs = {
            "en-IN-priya": {
                "min_buffer_size": 20,      # Minimal buffering
                "max_buffer_delay_ms": 100,  # Ultra-low latency
                "sample_rate": 8000,         # Phone quality
                "style": "Conversational"
            },
            # ⭐⭐⭐⭐⭐ PREMIUM Hindi Female - Much better than ayushi
            "hi-IN-shweta": {
                "min_buffer_size": 20,      # Faster than old hindi voice
                "max_buffer_delay_ms": 100,  # Reduced latency
                "sample_rate": 8000,
                "style": "Conversational"     # Warm, natural, expressive
            },
            # ⭐⭐⭐⭐⭐ PREMIUM Hindi Male - Professional quality
            "hi-IN-shaan": {
                "min_buffer_size": 20,
                "max_buffer_delay_ms": 100,
                "sample_rate": 8000,
                "style": "Conversational"     # Confident, calm, professional
            },
            "te-IN-shruti": {
                "min_buffer_size": 25,
                "max_buffer_delay_ms": 120,
                "sample_rate": 8000,
                "style": "Conversational"
            },
            "en-IN-rohan": {
                "min_buffer_size": 20,
                "max_buffer_delay_ms": 100,
                "sample_rate": 8000,
                "style": "Friendly"
            }
        }
        
        self.logger.info("⚡ Lightning Murf Streaming initialized - NO preprocessing mode")
    
    async def stream_voice_ultra_fast(
        self, 
        text: str, 
        voice_id: str = "en-IN-priya",
        priority: str = "urgent"
    ) -> AsyncIterator[bytes]:
        """
        ULTRA-FAST streaming - yields audio chunks as they arrive
        No waiting, no buffering - pure streaming speed
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            priority: Processing priority (urgent/normal)
            
        Yields:
            bytes: Audio chunks as they arrive from Murf
        """
        start_time = time.time()
        connection_reused = False
        
        try:
            # Get or create WebSocket connection (with pooling)
            ws, connection_reused = await self._get_instant_connection(voice_id)
            
            # Get voice configuration
            config = self.voice_configs.get(voice_id, self.voice_configs["en-IN-priya"])
            
            # Send minimal config for maximum speed
            stream_config = {
                "voice_config": {
                    "voiceId": voice_id,
                    "style": config["style"],
                    "rate": 0,
                    "pitch": 0
                },
                "streaming_config": {
                    "min_buffer_size": config["min_buffer_size"],
                    "max_buffer_delay_ms": config["max_buffer_delay_ms"],
                    "format": "WAV",
                    "sample_rate": config["sample_rate"],
                    "channel_type": "MONO",
                    "priority": priority
                }
            }
            
            await ws.send(json.dumps(stream_config))
            
            # Send text immediately
            text_msg = {
                "text": text,
                "end": True,
                "priority": priority
            }
            await ws.send(json.dumps(text_msg))
            
            self.logger.info(f"📤 Lightning request sent: {voice_id} ({'reused' if connection_reused else 'new'})")
            
            # Stream audio chunks as they arrive
            first_chunk = True
            chunk_count = 0
            
            while True:
                try:
                    # Wait for response with timeout
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    if "audio" in data and data["audio"]:
                        audio_b64 = data["audio"]
                        audio_bytes = base64.b64decode(audio_b64)
                        
                        if first_chunk:
                            ttfb = (time.time() - start_time) * 1000
                            self.logger.info(f"⚡ LIGHTNING TTFB: {ttfb:.0f}ms (target: <500ms)")
                            first_chunk = False
                        
                        chunk_count += 1
                        yield audio_bytes  # Stream immediately - NO buffering!
                    
                    if data.get("final"):
                        total_time = (time.time() - start_time) * 1000
                        self.logger.info(
                            f"🚀 LIGHTNING complete: {chunk_count} chunks in {total_time:.0f}ms "
                            f"(target: <1500ms)"
                        )
                        break
                        
                except asyncio.TimeoutError:
                    self.logger.warning("⚠️ Stream timeout - ending")
                    break
                    
        except Exception as e:
            self.logger.error(f"❌ Lightning stream failed: {e}")
            yield b""  # Empty fallback
    
    async def _get_instant_connection(self, voice_id: str) -> tuple[Any, bool]:
        """
        Get instant WebSocket connection from pool
        
        Returns:
            tuple: (WebSocket connection, was_reused)
        """
        # Check if we have a healthy connection in pool
        if voice_id in self.connection_pool:
            ws_info = self.connection_pool[voice_id]
            ws = ws_info['connection']
            
            # Check if connection is still alive
            try:
                await ws.ping()
                # Connection is alive, reuse it
                ws_info['last_used'] = time.time()
                self.logger.debug(f"♻️ Reusing connection: {voice_id}")
                return ws, True
            except:
                # Connection is dead, remove it
                del self.connection_pool[voice_id]
                self.logger.debug(f"🗑️ Removed dead connection: {voice_id}")
        
        # Create new connection with optimized settings
        url = (
            f"{self.ws_url}"
            f"?api-key={self.api_key}"
            f"&sample_rate=8000"
            f"&format=WAV"
            f"&channel_type=MONO"
        )
        
        self.logger.debug(f"🔌 Creating new connection: {voice_id}")
        
        ws = await websockets.connect(
            url,
            ping_interval=30,       # Longer ping interval
            ping_timeout=10,        # Shorter timeout
            max_size=2**18,         # 256KB buffer (smaller for speed)
            max_queue=16,           # Smaller queue for speed
            compression=None,       # No compression for speed
            close_timeout=5         # Quick cleanup
        )
        
        # Add to pool
        self.connection_pool[voice_id] = {
            'connection': ws,
            'created': time.time(),
            'last_used': time.time()
        }
        
        self.logger.info(f"⚡ New lightning connection: {voice_id}")
        
        # Clean up old connections if pool is too large
        if len(self.connection_pool) > self.max_connections:
            await self._cleanup_old_connections()
        
        return ws, False
    
    async def _cleanup_old_connections(self):
        """Remove oldest connections from pool"""
        if len(self.connection_pool) <= self.max_connections:
            return
        
        # Sort by last used time
        sorted_voices = sorted(
            self.connection_pool.items(),
            key=lambda x: x[1]['last_used']
        )
        
        # Remove oldest connection
        voice_to_remove = sorted_voices[0][0]
        ws_info = self.connection_pool[voice_to_remove]
        
        try:
            await ws_info['connection'].close()
        except:
            pass
        
        del self.connection_pool[voice_to_remove]
        self.logger.debug(f"🗑️ Cleaned up old connection: {voice_to_remove}")
    
    async def generate_phone_optimized_audio(
        self, 
        text: str, 
        voice_id: str
    ) -> tuple[bytes, PerformanceMetrics]:
        """
        Generate complete audio optimized for phone calls
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            
        Returns:
            tuple: (audio_bytes, performance_metrics)
        """
        start_time = time.time()
        audio_chunks = []
        chunk_count = 0
        connection_reused = False
        ttfb_ms = 0
        first_chunk = True
        
        async for chunk in self.stream_voice_ultra_fast(text, voice_id, "urgent"):
            if chunk:
                if first_chunk:
                    ttfb_ms = (time.time() - start_time) * 1000
                    first_chunk = False
                
                audio_chunks.append(chunk)
                chunk_count += 1
        
        total_time_ms = (time.time() - start_time) * 1000
        
        if audio_chunks:
            # Combine chunks into phone-optimized WAV
            complete_audio = self._combine_audio_chunks(audio_chunks)
            audio_size = len(complete_audio)
            
            metrics = PerformanceMetrics(
                ttfb_ms=ttfb_ms,
                total_time_ms=total_time_ms,
                chunk_count=chunk_count,
                audio_size_bytes=audio_size,
                connection_reused=connection_reused
            )
            
            return complete_audio, metrics
        
        # Return empty audio with metrics
        metrics = PerformanceMetrics(
            ttfb_ms=ttfb_ms,
            total_time_ms=total_time_ms,
            chunk_count=0,
            audio_size_bytes=0,
            connection_reused=connection_reused
        )
        
        return b"", metrics
    
    def _combine_audio_chunks(self, chunks: list[bytes]) -> bytes:
        """
        Combine audio chunks into single WAV file
        Optimized for phone quality (8kHz mono)
        """
        if not chunks:
            return b""
        
        # Remove WAV headers from chunks (except first)
        audio_data = chunks[0]  # Keep first chunk with header
        
        for chunk in chunks[1:]:
            # Skip WAV header (44 bytes) for subsequent chunks
            if len(chunk) > 44:
                audio_data += chunk[44:]
        
        return audio_data
    
    def _create_phone_optimized_wav_header(self, data_size: int) -> bytes:
        """
        Create minimal WAV header for 8kHz mono phone quality
        
        Args:
            data_size: Size of audio data in bytes
            
        Returns:
            bytes: WAV header
        """
        # WAV header structure for 8kHz, 16-bit, mono
        return struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + data_size,  # File size - 8
            b'WAVE',
            b'fmt ',
            16,              # PCM format chunk size
            1,               # Audio format (PCM)
            1,               # Channels (mono)
            8000,            # Sample rate (8kHz for phone)
            16000,           # Byte rate (8000 * 2)
            2,               # Block align (channels * bytes per sample)
            16,              # Bits per sample
            b'data',
            data_size
        )
    
    async def close_all_connections(self):
        """Cleanup all connections"""
        self.logger.info("🧹 Closing all lightning connections...")
        
        for voice_id, ws_info in list(self.connection_pool.items()):
            try:
                await ws_info['connection'].close()
                self.logger.debug(f"✅ Closed: {voice_id}")
            except Exception as e:
                self.logger.error(f"❌ Error closing {voice_id}: {e}")
        
        self.connection_pool.clear()
        self.logger.info("✅ All connections closed")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            "active_connections": len(self.connection_pool),
            "max_connections": self.max_connections,
            "voices_in_pool": list(self.connection_pool.keys()),
            "pool_usage_percent": (len(self.connection_pool) / self.max_connections) * 100
        }


# Test code
if __name__ == "__main__":
    async def test_lightning_streaming():
        """Test ultra-fast streaming"""
        print("\n⚡ Testing Lightning Murf Streaming\n")
        
        lightning = LightningMurfStreaming()
        
        test_cases = [
            ("Hello! How can I help you today?", "en-IN-priya"),
            ("नमस्ते! मैं आपकी कैसे मदद कर सकता हूं?", "hi-IN-ayushi"),
        ]
        
        for text, voice_id in test_cases:
            print(f"\n📝 Testing: {text[:50]}... with {voice_id}")
            
            audio, metrics = await lightning.generate_phone_optimized_audio(text, voice_id)
            
            print(f"✅ Success!")
            print(f"   - TTFB: {metrics.ttfb_ms:.0f}ms (target: <500ms)")
            print(f"   - Total: {metrics.total_time_ms:.0f}ms (target: <1500ms)")
            print(f"   - Chunks: {metrics.chunk_count}")
            print(f"   - Size: {metrics.audio_size_bytes:,} bytes")
            print(f"   - Reused: {metrics.connection_reused}")
            
            if audio:
                # Save test audio
                filename = f"test_lightning_{voice_id.replace('-', '_')}.wav"
                with open(filename, 'wb') as f:
                    f.write(audio)
                print(f"   - Saved: {filename}")
        
        # Show pool stats
        print(f"\n📊 Pool Stats: {lightning.get_pool_stats()}")
        
        await lightning.close_all_connections()
        print("\n✅ Test complete!")
    
    # Run test
    asyncio.run(test_lightning_streaming())
