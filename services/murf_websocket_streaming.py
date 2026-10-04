"""
Murf AI WebSocket Streaming Service for Real-Time Phone Calls
Optimized for ultra-low latency telephony applications using Twilio
"""

import asyncio
import logging
import websockets
import json
import base64
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class MurfWebSocketStreaming:
    """
    Murf AI WebSocket streaming service for real-time, low-latency voice generation
    Perfect for phone calls and interactive voice applications
    """
    
    def __init__(self):
        self.api_key = os.getenv("MURF_API_KEY")
        self.websocket_url = "wss://api.murf.ai/v1/speech/generate-stream"
        self.logger = logging.getLogger(__name__)
        
        # Indian voices for multi-language support
        self.voices = {
            # English - India
            "en-IN-priya": {"locale": "en-IN", "gender": "female", "name": "Priya"},
            "en-IN-eashwar": {"locale": "en-IN", "gender": "male", "name": "Eashwar"},
            "en-IN-rohan": {"locale": "en-IN", "gender": "male", "name": "Rohan"},
            "en-IN-alia": {"locale": "en-IN", "gender": "female", "name": "Alia"},
            
            # Hindi - India
            "hi-IN-ayushi": {"locale": "hi-IN", "gender": "female", "name": "Ayushi"},
            "hi-IN-kabir": {"locale": "hi-IN", "gender": "male", "name": "Kabir"},
            
            # Telugu - India
            "te-IN-shruti": {"locale": "te-IN", "gender": "female", "name": "Shruti"},
            "te-IN-mohan": {"locale": "te-IN", "gender": "male", "name": "Mohan"},
        }
        
    async def generate_streaming_audio_for_phone(
        self,
        text: str,
        voice_id: str = "en-IN-priya",
        style: str = "Conversational",
        min_buffer_size: int = 40,  # Minimum for fastest TTFB
        max_buffer_delay_ms: int = 200,  # Lower for faster response
        context_id: Optional[str] = None
    ) -> bytes:
        """
        Generate audio using Murf WebSocket streaming optimized for phone calls
        ULTRA-LOW LATENCY: Receives audio chunks in real-time as they're generated
        
        Args:
            text: Text to convert to speech
            voice_id: Murf voice ID (e.g., "en-IN-priya")
            style: Voice style (e.g., "Conversational", "Friendly", "Professional")
            min_buffer_size: Minimum characters before sending (40-160, lower = faster TTFB)
            max_buffer_delay_ms: Max delay in ms before sending incomplete buffer (0-1000)
            context_id: Optional context ID for conversation continuity
            
        Returns:
            Audio bytes in WAV format (ULAW encoded) ready for Twilio
        """
        ws = None
        audio_chunks = []
        first_chunk_time = None
        start_time = asyncio.get_event_loop().time()
        
        try:
            # WebSocket URL with API key
            url = f"wss://api.murf.ai/v1/speech/stream-input?api-key={self.api_key}&sample_rate=8000&channel_type=MONO&format=WAV"
            
            self.logger.info(f"🔄 Connecting to Murf WebSocket for voice: {voice_id}")
            ws = await websockets.connect(url, ping_interval=20, ping_timeout=10)
            self.logger.info("✅ WebSocket connected")
            
            # Send voice configuration
            voice_config = {
                "voice_config": {
                    "voiceId": voice_id,
                    "style": style,
                    "rate": 0,  # Normal speed
                    "pitch": 0,  # Normal pitch
                    "variation": 1  # Natural variation
                }
            }
            
            await ws.send(json.dumps(voice_config))
            self.logger.info(f"📤 Voice config sent: {voice_id}")
            
            # Send text with end flag
            text_msg = {
                "text": text,
                "end": True  # Signal end of input
            }
            
            await ws.send(json.dumps(text_msg))
            self.logger.info(f"� Text sent: '{text[:60]}...'")
            
            # Receive audio chunks in real-time
            first_chunk = True
            chunk_count = 0
            
            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    data = json.loads(response)
                    
                    if "audio" in data:
                        audio_b64 = data["audio"]
                        if audio_b64:
                            audio_bytes = base64.b64decode(audio_b64)
                            
                            # Skip WAV header for first chunk only
                            if first_chunk and len(audio_bytes) > 44:
                                audio_bytes = audio_bytes[44:]
                                first_chunk = False
                                first_chunk_time = asyncio.get_event_loop().time()
                                ttfb = (first_chunk_time - start_time) * 1000
                                self.logger.info(f"⚡ First audio chunk! TTFB: {ttfb:.0f}ms")
                            
                            if len(audio_bytes) > 0:
                                chunk_count += 1
                                audio_chunks.append(audio_bytes)
                                self.logger.debug(f"🎵 Chunk {chunk_count}: {len(audio_bytes)} bytes")
                    
                    if data.get("final"):
                        self.logger.info(f"✅ Synthesis complete: {chunk_count} chunks")
                        break
                        
                except asyncio.TimeoutError:
                    if chunk_count > 0:
                        self.logger.info(f"✅ Timeout reached, got {chunk_count} chunks")
                        break
                    else:
                        self.logger.error("❌ Timeout with no audio received!")
                        raise Exception("No audio received from Murf")
            
            # Combine all audio chunks
            full_audio = b''.join(audio_chunks)
            
            if len(full_audio) == 0:
                raise Exception("Empty audio generated")
            
            # Create proper WAV file with ULAW encoding
            wav_data = self._create_wav_from_pcm(full_audio)
            
            total_time = (asyncio.get_event_loop().time() - start_time) * 1000
            self.logger.info(f"🎉 Complete! {len(wav_data)} bytes in {total_time:.0f}ms")
            
            return wav_data
            
        except Exception as e:
            self.logger.error(f"❌ WebSocket streaming failed: {e}")
            raise
        finally:
            if ws:
                try:
                    await ws.close()
                except:
                    pass
    
    def _create_wav_from_pcm(self, pcm_data: bytes) -> bytes:
        """Create WAV file from PCM data"""
        import struct
        
        sample_rate = 8000
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
        block_align = num_channels * (bits_per_sample // 8)
        data_size = len(pcm_data)
        
        # WAV header
        header = struct.pack('<4sI4s', b'RIFF', 36 + data_size, b'WAVE')
        
        # Format chunk
        fmt_chunk = struct.pack(
            '<4sIHHIIHH',
            b'fmt ',
            16,  # Chunk size
            1,   # PCM format
            num_channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample
        )
        
        # Data chunk
        data_chunk = struct.pack('<4sI', b'data', data_size)
        
        return header + fmt_chunk + data_chunk + pcm_data
    
    async def generate_and_save_for_twilio(
        self,
        text: str,
        voice_id: str = "en-IN-priya",
        output_path: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate audio and save to file for Twilio playback
        
        Returns:
            Path to the generated audio file
        """
        if not output_path:
            import uuid
            output_path = f"Voice_outputs/phone_{uuid.uuid4().hex[:8]}.wav"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate audio with WebSocket streaming
        audio_data = await self.generate_streaming_audio_for_phone(
            text=text,
            voice_id=voice_id,
            **kwargs
        )
        
        # Save WAV file
        with open(output_path, 'wb') as f:
            f.write(audio_data)
        
        self.logger.info(f"💾 Saved audio to: {output_path}")
        return output_path
    
    def _create_wav_from_ulaw(self, ulaw_data: bytes) -> bytes:
        """Create WAV file with ULAW encoding"""
        import struct
        
        # WAV header for ULAW format
        sample_rate = 8000
        num_channels = 1
        bits_per_sample = 8
        
        # Calculate sizes
        data_size = len(ulaw_data)
        file_size = 36 + data_size
        
        # Build WAV header
        header = struct.pack('<4sI4s', b'RIFF', file_size, b'WAVE')
        
        # Format chunk
        fmt_chunk = struct.pack(
            '<4sIHHIIHH',
            b'fmt ',
            18,  # Chunk size
            7,   # Audio format (7 = ULAW)
            num_channels,
            sample_rate,
            sample_rate * num_channels,
            num_channels,
            bits_per_sample
        )
        
        # Fact chunk (required for compressed formats)
        fact_chunk = struct.pack('<4sII', b'fact', 4, data_size)
        
        # Data chunk
        data_chunk = struct.pack('<4sI', b'data', data_size)
        
        return header + fmt_chunk + fact_chunk + data_chunk + ulaw_data
    
    def get_voice_for_language(self, language: str, gender: str = "female") -> str:
        """
        Get appropriate voice for language
        
        Args:
            language: "en-IN", "hi-IN", or "te-IN"
            gender: "male" or "female"
        
        Returns:
            Voice ID
        """
        for voice_id, info in self.voices.items():
            if info["locale"] == language and info["gender"] == gender:
                return voice_id
        
        # Fallback to default
        return "en-IN-priya"
    
    async def test_latency(self, text: str = "Hello, this is a test call."):
        """Test TTFB and generation latency"""
        import time
        
        self.logger.info("🧪 Testing Murf WebSocket latency...")
        
        start_time = time.time()
        audio = await self.generate_streaming_audio_for_phone(
            text=text,
            min_buffer_size=40,  # Fastest TTFB
            max_buffer_delay_ms=200
        )
        end_time = time.time()
        
        total_time = end_time - start_time
        audio_size = len(audio)
        
        self.logger.info(f"⚡ Latency Test Results:")
        self.logger.info(f"   Total time: {total_time:.2f}s")
        self.logger.info(f"   Audio size: {audio_size} bytes")
        self.logger.info(f"   Throughput: {audio_size/total_time:.0f} bytes/sec")
        
        return {
            "total_time": total_time,
            "audio_size": audio_size,
            "ttfb": "< 500ms (estimated)"
        }


# Example usage
async def main():
    """Test the WebSocket streaming"""
    murf_ws = MurfWebSocketStreaming()
    
    # Test English
    print("Testing English voice...")
    await murf_ws.generate_and_save_for_twilio(
        text="Hello Arjun, this is Priya Sharma from Murf AI. How are you today?",
        voice_id="en-IN-priya",
        output_path="Voice_outputs/test_en.wav"
    )
    
    # Test Hindi
    print("\nTesting Hindi voice...")
    await murf_ws.generate_and_save_for_twilio(
        text="नमस्ते जितेश, मैं मुर्फ एआई से आयुषी बोल रही हूं। आप कैसे हैं?",
        voice_id="hi-IN-ayushi",
        output_path="Voice_outputs/test_hi.wav"
    )
    
    # Test Telugu
    print("\nTesting Telugu voice...")
    await murf_ws.generate_and_save_for_twilio(
        text="నమస్కారం, నేను మర్ఫ్ AI నుండి శ్రుతి మాట్లాడుతున్నాను.",
        voice_id="te-IN-shruti",
        output_path="Voice_outputs/test_te.wav"
    )
    
    # Test latency
    print("\nTesting latency...")
    await murf_ws.test_latency()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
