import asyncio
import logging
from typing import Dict, Any, Optional
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say
import os
from dotenv import load_dotenv

load_dotenv()

class TwilioPhoneService:
    """
    Twilio integration for real phone calls with 2-way voice communication
    Makes outbound calls to prospects and handles inbound calls
    """
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.logger = logging.getLogger(__name__)
        
        self.client = None
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize Twilio client"""
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            self.logger.warning("⚠️ Twilio credentials not configured - phone calling disabled")
            self.logger.info("💡 Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER to .env")
            return False
            
        try:
            self.client = Client(self.account_sid, self.auth_token)
            # Test connection
            self.client.api.accounts(self.account_sid).fetch()
            self.logger.info(f"✅ Twilio initialized - Phone: {self.phone_number}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Twilio initialization failed: {e}")
            return False
    
    async def make_outbound_call(
        self,
        to_number: str,
        call_type: str = "b2b_sales",
        lead_info: Dict[str, Any] = None,
        webhook_url: str = None
    ) -> Dict[str, Any]:
        """
        Make an outbound call to a prospect
        
        Args:
            to_number: Phone number to call (E.164 format: +1234567890)
            call_type: 'b2b_sales' or 'real_estate'
            lead_info: Information about the lead
            webhook_url: Your server webhook URL for handling call events
            
        Returns:
            Call information including SID
        """
        if not self.client:
            return {"error": "Twilio not initialized"}
        
        try:
            # Generate TwiML for the call
            twiml_url = f"{webhook_url}/api/phone/twiml/{call_type}"
            
            self.logger.info(f"📞 Making outbound call to {to_number} (type: {call_type})")
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=twiml_url,
                status_callback=f"{webhook_url}/api/phone/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                record=True,  # Record the call
                recording_status_callback=f"{webhook_url}/api/phone/recording"
            )
            
            # Store call info
            self.active_calls[call.sid] = {
                "sid": call.sid,
                "to_number": to_number,
                "call_type": call_type,
                "lead_info": lead_info or {},
                "status": "initiated",
                "start_time": None,
                "end_time": None
            }
            
            self.logger.info(f"✅ Call initiated - SID: {call.sid}")
            
            return {
                "success": True,
                "call_sid": call.sid,
                "to_number": to_number,
                "from_number": self.phone_number,
                "status": "initiated",
                "message": f"Call initiated to {to_number}"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Outbound call failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_twiml_b2b_sales(self, call_sid: str = None) -> str:
        """Generate TwiML for B2B sales call"""
        response = VoiceResponse()
        
        # Initial greeting
        response.say(
            "Hello! This is Alex from AI Solutions. "
            "I'm calling to discuss how our AI platform can help streamline your business operations. "
            "Do you have a few minutes to talk?",
            voice='Polly.Aditi',
            language='en-IN'
        )
        
        # Gather response with speech recognition
        gather = Gather(
            input='speech',
            timeout=3,
            speech_timeout='auto',
            action='/api/phone/process-speech/b2b_sales',
            method='POST'
        )
        response.append(gather)
        
        # If no input, prompt again
        response.say(
            "I didn't catch that. Are you available to discuss our AI solutions?",
            voice='Polly.Aditi',
            language='en-IN'
        )
        
        return str(response)
    
    def generate_twiml_real_estate(self, call_sid: str = None) -> str:
        """Generate TwiML for real estate call"""
        response = VoiceResponse()
        
        # Initial greeting (Hindi + English)
        response.say(
            "Namaste! I'm calling from Prime Properties regarding your property inquiry. "
            "Are you still looking for properties in your preferred area?",
            voice='Polly.Aditi',
            language='en-IN'
        )
        
        # Gather response
        gather = Gather(
            input='speech',
            timeout=3,
            speech_timeout='auto',
            action='/api/phone/process-speech/real_estate',
            method='POST'
        )
        response.append(gather)
        
        response.say(
            "I didn't hear you. Should I call back later?",
            voice='Polly.Aditi',
            language='en-IN'
        )
        
        return str(response)
    
    def generate_twiml_response(
        self,
        message: str,
        next_action: str = None,
        end_call: bool = False
    ) -> str:
        """Generate TwiML response based on conversation flow"""
        response = VoiceResponse()
        
        # Speak the AI's response
        response.say(
            message,
            voice='Polly.Aditi',
            language='en-IN'
        )
        
        if end_call:
            response.say(
                "Thank you for your time. Have a great day!",
                voice='Polly.Aditi',
                language='en-IN'
            )
            response.hangup()
        else:
            # Continue gathering input
            gather = Gather(
                input='speech',
                timeout=3,
                speech_timeout='auto',
                action=next_action or '/api/phone/process-speech/continue',
                method='POST'
            )
            response.append(gather)
            
            # Timeout fallback
            response.say(
                "Are you still there?",
                voice='Polly.Aditi',
                language='en-IN'
            )
        
        return str(response)
    
    async def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """Get current status of a call"""
        if not self.client:
            return {"error": "Twilio not initialized"}
        
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "from": call.from_,
                "to": call.to,
                "price": call.price,
                "direction": call.direction
            }
        except Exception as e:
            self.logger.error(f"❌ Failed to get call status: {e}")
            return {"error": str(e)}
    
    async def end_call(self, call_sid: str) -> Dict[str, Any]:
        """End an active call"""
        if not self.client:
            return {"error": "Twilio not initialized"}
        
        try:
            call = self.client.calls(call_sid).update(status='completed')
            
            if call_sid in self.active_calls:
                self.active_calls[call_sid]["status"] = "completed"
            
            self.logger.info(f"✅ Call ended - SID: {call_sid}")
            return {
                "success": True,
                "call_sid": call_sid,
                "status": "completed"
            }
        except Exception as e:
            self.logger.error(f"❌ Failed to end call: {e}")
            return {"error": str(e)}
    
    async def get_recording_url(self, call_sid: str) -> Optional[str]:
        """Get recording URL for a completed call"""
        if not self.client:
            return None
        
        try:
            recordings = self.client.recordings.list(call_sid=call_sid, limit=1)
            if recordings:
                recording = recordings[0]
                return f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}"
            return None
        except Exception as e:
            self.logger.error(f"❌ Failed to get recording: {e}")
            return None
    
    async def send_sms(
        self,
        to_number: str,
        message: str
    ) -> Dict[str, Any]:
        """Send SMS follow-up message"""
        if not self.client:
            return {"error": "Twilio not initialized"}
        
        try:
            sms = self.client.messages.create(
                to=to_number,
                from_=self.phone_number,
                body=message
            )
            
            self.logger.info(f"✅ SMS sent to {to_number}")
            return {
                "success": True,
                "sid": sms.sid,
                "to_number": to_number
            }
        except Exception as e:
            self.logger.error(f"❌ SMS failed: {e}")
            return {"error": str(e)}
