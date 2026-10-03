import asyncio
import logging
import numpy as np
import io
import wave
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import time

class AudioProcessor:
    """Optimized real-time audio processing for ultra-low latency"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Audio configuration for optimal quality
        self.sample_rate = 16000  # Azure STT optimal
        self.channels = 1  # Mono for efficiency
        self.chunk_duration = 0.25  # 250ms chunks for real-time feel
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
        # Processing queues for different stages
        self.audio_queues = {}
        self.processing_stats = {
            "chunks_processed": 0,
            "avg_processing_time": 0,
            "queue_sizes": {},
            "last_activity": None
        }
        
        # Voice Activity Detection (VAD)
        self.vad_threshold = 0.01  # Minimum energy for speech
        self.silence_duration = 1.0  # Seconds of silence before pause
        
    async def initialize_session(self, session_id: str, callback_handler: Callable) -> bool:
        """Initialize audio processing session"""
        try:
            self.audio_queues[session_id] = {
                "raw_audio": asyncio.Queue(maxsize=20),  # 5 seconds buffer
                "processed_audio": asyncio.Queue(maxsize=10),
                "callback_handler": callback_handler,
                "buffer": bytearray(),
                "last_speech_time": time.time(),
                "silence_detector": SilenceDetector(),
                "session_stats": {
                    "start_time": time.time(),
                    "total_audio_seconds": 0,
                    "speech_segments": 0,
                    "silence_segments": 0
                }
            }
            
            # Start processing task for this session
            asyncio.create_task(self._process_session_audio(session_id))
            
            self.logger.info(f"Audio processor initialized for session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audio processor for {session_id}: {e}")
            return False
    
    async def process_audio_chunk(self, session_id: str, audio_data: bytes) -> bool:
        """Process incoming audio chunk with VAD and optimization"""
        if session_id not in self.audio_queues:
            return False
        
        try:
            session_queue = self.audio_queues[session_id]
            
            # Convert to numpy array for processing
            audio_array = self._bytes_to_numpy(audio_data)
            
            # Voice Activity Detection
            is_speech, energy_level = self._detect_voice_activity(audio_array)
            
            # Add to buffer if speech detected or continuing speech
            current_time = time.time()
            
            if is_speech:
                session_queue["last_speech_time"] = current_time
                session_queue["buffer"].extend(audio_data)
                session_queue["session_stats"]["speech_segments"] += 1
            else:
                # Check if we should process accumulated buffer
                silence_duration = current_time - session_queue["last_speech_time"]
                
                if silence_duration > self.silence_duration and len(session_queue["buffer"]) > 0:
                    # Process accumulated speech segment
                    await self._process_speech_segment(session_id, bytes(session_queue["buffer"]))
                    session_queue["buffer"] = bytearray()
                    session_queue["session_stats"]["silence_segments"] += 1
            
            # Update session stats
            session_queue["session_stats"]["total_audio_seconds"] += self.chunk_duration
            self.processing_stats["chunks_processed"] += 1
            self.processing_stats["last_activity"] = current_time
            
            return True
            
        except Exception as e:
            self.logger.error(f"Audio processing error for {session_id}: {e}")
            return False
    
    async def _process_session_audio(self, session_id: str):
        """Background task to process audio for a session"""
        session_queue = self.audio_queues[session_id]
        
        while session_id in self.audio_queues:
            try:
                # Wait for audio data with timeout
                audio_chunk = await asyncio.wait_for(
                    session_queue["raw_audio"].get(), 
                    timeout=5.0
                )
                
                start_time = time.time()
                
                # Process the audio chunk
                processed_result = await self._enhance_audio_quality(audio_chunk)
                
                # Call the registered callback
                if session_queue["callback_handler"]:
                    await session_queue["callback_handler"](session_id, processed_result)
                
                # Update performance stats
                processing_time = time.time() - start_time
                self._update_processing_stats(processing_time)
                
            except asyncio.TimeoutError:
                # No audio received, continue listening
                continue
            except Exception as e:
                self.logger.error(f"Session audio processing error: {e}")
                break
    
    async def _process_speech_segment(self, session_id: str, speech_data: bytes):
        """Process a complete speech segment"""
        try:
            session_queue = self.audio_queues[session_id]
            
            # Enhance audio quality
            enhanced_audio = await self._enhance_audio_quality(speech_data)
            
            # Add to processing queue
            await session_queue["processed_audio"].put({
                "audio_data": enhanced_audio,
                "timestamp": time.time(),
                "duration": len(speech_data) / (self.sample_rate * 2),  # Duration in seconds
                "session_id": session_id
            })
            
        except Exception as e:
            self.logger.error(f"Speech segment processing error: {e}")
    
    async def _enhance_audio_quality(self, audio_data: bytes) -> bytes:
        """Enhance audio quality for better STT recognition"""
        try:
            # Convert to numpy for processing
            audio_array = self._bytes_to_numpy(audio_data)
            
            # Apply noise reduction (simple high-pass filter)
            audio_array = self._apply_highpass_filter(audio_array)
            
            # Normalize volume
            audio_array = self._normalize_audio(audio_array)
            
            # Apply light compression for consistent levels
            audio_array = self._apply_compression(audio_array)
            
            # Convert back to bytes
            return self._numpy_to_bytes(audio_array)
            
        except Exception as e:
            self.logger.error(f"Audio enhancement error: {e}")
            return audio_data  # Return original if enhancement fails
    
    def _bytes_to_numpy(self, audio_bytes: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array"""
        return np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    
    def _numpy_to_bytes(self, audio_array: np.ndarray) -> bytes:
        """Convert numpy array back to bytes"""
        # Clip to prevent overflow
        audio_array = np.clip(audio_array, -1.0, 1.0)
        # Convert to int16
        audio_int16 = (audio_array * 32767).astype(np.int16)
        return audio_int16.tobytes()
    
    def _detect_voice_activity(self, audio_array: np.ndarray) -> tuple[bool, float]:
        """Simple voice activity detection"""
        # Calculate RMS energy
        rms_energy = np.sqrt(np.mean(audio_array ** 2))
        
        # Check if energy is above threshold
        is_speech = rms_energy > self.vad_threshold
        
        return is_speech, rms_energy
    
    def _apply_highpass_filter(self, audio_array: np.ndarray, cutoff_freq: float = 100.0) -> np.ndarray:
        """Apply simple high-pass filter to remove low-frequency noise"""
        # Simple high-pass filter implementation
        # In production, use scipy.signal for better filtering
        
        # Calculate filter coefficient
        rc = 1.0 / (cutoff_freq * 2 * np.pi)
        dt = 1.0 / self.sample_rate
        alpha = rc / (rc + dt)
        
        # Apply filter
        filtered = np.zeros_like(audio_array)
        filtered[0] = audio_array[0]
        
        for i in range(1, len(audio_array)):
            filtered[i] = alpha * (filtered[i-1] + audio_array[i] - audio_array[i-1])
        
        return filtered
    
    def _normalize_audio(self, audio_array: np.ndarray) -> np.ndarray:
        """Normalize audio amplitude"""
        max_val = np.max(np.abs(audio_array))
        if max_val > 0:
            # Normalize to 70% of full scale to prevent clipping
            return audio_array * (0.7 / max_val)
        return audio_array
    
    def _apply_compression(self, audio_array: np.ndarray, threshold: float = 0.5, ratio: float = 3.0) -> np.ndarray:
        """Apply simple audio compression"""
        compressed = np.copy(audio_array)
        
        # Find samples above threshold
        mask = np.abs(compressed) > threshold
        
        # Apply compression to samples above threshold
        compressed[mask] = np.sign(compressed[mask]) * (
            threshold + (np.abs(compressed[mask]) - threshold) / ratio
        )
        
        return compressed
    
    def _update_processing_stats(self, processing_time: float):
        """Update performance statistics"""
        count = self.processing_stats["chunks_processed"]
        current_avg = self.processing_stats["avg_processing_time"]
        
        # Update rolling average
        self.processing_stats["avg_processing_time"] = (
            (current_avg * (count - 1) + processing_time) / count
        )
        
        # Update queue sizes
        for session_id, queue_data in self.audio_queues.items():
            self.processing_stats["queue_sizes"][session_id] = {
                "raw_audio": queue_data["raw_audio"].qsize(),
                "processed_audio": queue_data["processed_audio"].qsize(),
                "buffer_size": len(queue_data["buffer"])
            }
    
    async def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific session"""
        if session_id not in self.audio_queues:
            return None
        
        session_data = self.audio_queues[session_id]
        session_stats = session_data["session_stats"]
        
        current_time = time.time()
        session_duration = current_time - session_stats["start_time"]
        
        return {
            "session_id": session_id,
            "duration_seconds": session_duration,
            "total_audio_seconds": session_stats["total_audio_seconds"],
            "speech_segments": session_stats["speech_segments"],
            "silence_segments": session_stats["silence_segments"],
            "speech_ratio": session_stats["total_audio_seconds"] / session_duration if session_duration > 0 else 0,
            "queue_status": self.processing_stats["queue_sizes"].get(session_id, {}),
            "last_activity": self.processing_stats["last_activity"]
        }
    
    async def finalize_session(self, session_id: str):
        """Clean up session resources"""
        if session_id in self.audio_queues:
            session_data = self.audio_queues[session_id]
            
            # Process any remaining audio in buffer
            if len(session_data["buffer"]) > 0:
                await self._process_speech_segment(session_id, bytes(session_data["buffer"]))
            
            # Remove session
            del self.audio_queues[session_id]
            
            self.logger.info(f"Audio processor session finalized: {session_id}")

class SilenceDetector:
    """Helper class for detecting silence patterns"""
    
    def __init__(self, threshold: float = 0.005, min_silence_duration: float = 0.5):
        self.threshold = threshold
        self.min_silence_duration = min_silence_duration
        self.silence_start_time = None
        self.is_in_silence = False
    
    def detect_silence(self, audio_energy: float, current_time: float) -> bool:
        """Detect if we're in a silence period"""
        
        if audio_energy < self.threshold:
            # We're in silence
            if not self.is_in_silence:
                # Start of silence
                self.silence_start_time = current_time
                self.is_in_silence = True
            
            # Check if we've been silent long enough
            silence_duration = current_time - self.silence_start_time
            return silence_duration >= self.min_silence_duration
        else:
            # We're not in silence
            self.is_in_silence = False
            self.silence_start_time = None
            return False
