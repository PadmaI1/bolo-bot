import asyncio
import json
import logging
import time
from typing import Dict, Set, Callable, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import numpy as np

class WebSocketManager:
    """Optimized WebSocket manager for ultra-low latency voice processing"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.latency_stats = {
            "audio_received": [],
            "processing_time": [],
            "response_sent": []
        }
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register message handlers for different types"""
        self.message_handlers[message_type] = handler
    
    async def connect(self, websocket: WebSocket, session_id: str, industry: str) -> bool:
        """Accept WebSocket connection with optimized settings"""
        try:
            await websocket.accept()
            
            # Store connection with metadata
            self.active_connections[session_id] = websocket
            self.connection_metadata[session_id] = {
                "industry": industry,
                "connected_at": datetime.now(),
                "message_count": 0,
                "last_activity": datetime.now(),
                "audio_buffer": bytearray(),
                "processing_queue": asyncio.Queue(maxsize=10)  # Prevent memory buildup
            }
            
            self.logger.info(f"WebSocket connected: {session_id} ({industry})")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed for {session_id}: {e}")
            return False
    
    async def disconnect(self, session_id: str):
        """Clean disconnect with resource cleanup"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].close()
            except:
                pass
            
            del self.active_connections[session_id]
            if session_id in self.connection_metadata:
                del self.connection_metadata[session_id]
            
            self.logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Send message with error handling and performance tracking"""
        if session_id not in self.active_connections:
            return False
        
        try:
            start_time = time.time()
            websocket = self.active_connections[session_id]
            
            # Add timestamp to message
            message["timestamp"] = datetime.now().isoformat()
            
            await websocket.send_json(message)
            
            # Track response time
            response_time = (time.time() - start_time) * 1000
            self.latency_stats["response_sent"].append(response_time)
            
            # Update activity
            self.connection_metadata[session_id]["last_activity"] = datetime.now()
            self.connection_metadata[session_id]["message_count"] += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message to {session_id}: {e}")
            await self.disconnect(session_id)
            return False
    
    async def broadcast_audio_response(self, session_id: str, audio_data: bytes, text: str = ""):
        """Broadcast audio response with minimal latency"""
        message = {
            "type": "audio_response",
            "audio_data": audio_data.hex(),  # More efficient than base64
            "text": text,
            "format": "mp3",
            "sample_rate": 22050
        }
        
        await self.send_message(session_id, message)
    
    async def handle_audio_chunk(self, session_id: str, audio_data: bytes) -> bool:
        """Handle incoming audio with buffering and processing queue"""
        if session_id not in self.connection_metadata:
            return False
        
        try:
            metadata = self.connection_metadata[session_id]
            
            # Add to audio buffer
            metadata["audio_buffer"].extend(audio_data)
            
            # Process when buffer reaches optimal size (0.5 seconds of audio)
            target_buffer_size = 8000  # ~0.5 seconds at 16kHz
            
            if len(metadata["audio_buffer"]) >= target_buffer_size:
                # Extract buffer for processing
                audio_to_process = bytes(metadata["audio_buffer"])
                metadata["audio_buffer"] = bytearray()
                
                # Add to processing queue (non-blocking)
                try:
                    metadata["processing_queue"].put_nowait({
                        "audio_data": audio_to_process,
                        "received_at": time.time(),
                        "session_id": session_id
                    })
                except asyncio.QueueFull:
                    self.logger.warning(f"Processing queue full for {session_id}")
                    return False
                
                # Trigger handler if registered
                if "audio" in self.message_handlers:
                    asyncio.create_task(
                        self.message_handlers["audio"](session_id, audio_to_process)
                    )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Audio handling error for {session_id}: {e}")
            return False
    
    async def process_text_message(self, session_id: str, message: Dict[str, Any]):
        """Process text messages with appropriate handlers"""
        message_type = message.get("type", "unknown")
        
        if message_type in self.message_handlers:
            try:
                await self.message_handlers[message_type](session_id, message)
            except Exception as e:
                self.logger.error(f"Handler error for {message_type}: {e}")
                await self.send_message(session_id, {
                    "type": "error",
                    "message": f"Processing error: {str(e)}"
                })
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        active_count = len(self.active_connections)
        
        avg_latency = {
            "avg_response_time": np.mean(self.latency_stats["response_sent"][-100:]) if self.latency_stats["response_sent"] else 0,
            "max_response_time": np.max(self.latency_stats["response_sent"][-100:]) if self.latency_stats["response_sent"] else 0,
        }
        
        return {
            "active_connections": active_count,
            "total_messages_sent": sum(meta["message_count"] for meta in self.connection_metadata.values()),
            "average_latency_ms": avg_latency,
            "uptime_seconds": time.time() - getattr(self, 'start_time', time.time()),
        }
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        if session_id not in self.connection_metadata:
            return None
        
        metadata = self.connection_metadata[session_id]
        return {
            "session_id": session_id,
            "industry": metadata["industry"],
            "connected_at": metadata["connected_at"].isoformat(),
            "message_count": metadata["message_count"],
            "last_activity": metadata["last_activity"].isoformat(),
            "buffer_size": len(metadata["audio_buffer"]),
            "queue_size": metadata["processing_queue"].qsize()
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
