import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from ..azure_core.murf_tts import EnhancedMurfTTSService

class AppointmentSetterService:
    def __init__(self, tts_service: EnhancedMurfTTSService):
        self.tts_service = tts_service
        self.logger = logging.getLogger(__name__)
        
        # Active appointments
        self.scheduled_appointments = {}
        self.appointment_counter = 1000
        
        # Available time slots
        self.available_slots = {
            "weekdays": ["10:00", "11:30", "14:00", "15:30", "17:00"],
            "weekends": ["09:00", "10:30", "11:30", "14:00", "15:30", "16:30", "17:30"]
        }
        
        # Site visit types
        self.visit_types = {
            "individual_visit": {
                "duration": "45-60 minutes",
                "includes": ["Property walkthrough", "Amenity tour", "Documentation review", "Pricing discussion"],
                "staff": "Property consultant + Site engineer"
            },
            "group_visit": {
                "duration": "60-90 minutes", 
                "includes": ["Group presentation", "Property tour", "Q&A session", "Individual consultation"],
                "staff": "Senior sales manager + Property consultant"
            },
            "investor_visit": {
                "duration": "30-45 minutes",
                "includes": ["ROI presentation", "Market analysis", "Rental yield discussion", "Legal documentation"],
                "staff": "Investment advisor + Property consultant"
            }
        }
    
    def schedule_site_visit(self, lead_data: Dict[str, Any], property_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule property site visit"""
        try:
            appointment_id = f"APPT{self.appointment_counter}"
            self.appointment_counter += 1
            
            # Determine visit type based on lead profile
            visit_type = self._determine_visit_type(lead_data)
            
            # Get preferred time slots
            preferred_times = self._get_available_slots(
                preferences.get("preferred_date"),
                preferences.get("preferred_time_range", "anytime")
            )
            
            # Create appointment
            appointment = {
                "appointment_id": appointment_id,
                "lead_info": lead_data,
                "property_id": property_id,
                "visit_type": visit_type,
                "scheduled_date": preferences.get("preferred_date"),
                "scheduled_time": preferred_times[0] if preferred_times else "10:00",
                "duration": self.visit_types[visit_type]["duration"],
                "staff_assigned": self.visit_types[visit_type]["staff"],
                "visit_includes": self.visit_types[visit_type]["includes"],
                "appointment_status": "confirmed",
                "created_at": datetime.now().isoformat(),
                "confirmation_sent": False,
                "reminder_scheduled": False
            }
            
            self.scheduled_appointments[appointment_id] = appointment
            
            # Generate confirmation audio message
            confirmation_audio = await self._generate_appointment_confirmation(appointment)
            
            return {
                "status": "success",
                "appointment_id": appointment_id,
                "appointment_details": appointment,
                "confirmation_audio": confirmation_audio,
                "next_steps": [
                    "Send WhatsApp confirmation with location details",
                    "Schedule reminder call 24 hours before visit",
                    "Prepare property presentation materials"
                ]
            }
        
        except Exception as e:
            self.logger.error(f"Appointment scheduling error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _determine_visit_type(self, lead_data: Dict[str, Any]) -> str:
        """Determine appropriate visit type based on lead profile"""
        motivation = lead_data.get("motivation", "self_use")
        budget_range = lead_data.get("budget_range", "")
        family_size = lead_data.get("family_involvement", "self")
        
        if motivation == "investment":
            return "investor_visit"
        elif "family" in family_size.lower() or "joint" in family_size.lower():
            return "group_visit" 
        else:
            return "individual_visit"
    
    def _get_available_slots(self, preferred_date: str, time_range: str) -> List[str]:
        """Get available time slots for the preferred date"""
        try:
            if not preferred_date:
                # Default to this weekend
                today = datetime.now()
                days_ahead = 6 - today.weekday()  # Days until Saturday
                preferred_date = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            
            # Parse date and determine if weekday/weekend
            date_obj = datetime.strptime(preferred_date, "%Y-%m-%d")
            is_weekend = date_obj.weekday() >= 5  # Saturday=5, Sunday=6
            
            available_slots = self.available_slots["weekends" if is_weekend else "weekdays"]
            
            # Filter by time range preference
            if time_range == "morning":
                return [slot for slot in available_slots if int(slot.split(":")[0]) < 12]
            elif time_range == "afternoon":
                return [slot for slot in available_slots if 12 <= int(slot.split(":")[0]) < 17]
            elif time_range == "evening":
                return [slot for slot in available_slots if int(slot.split(":")[0]) >= 17]
            else:
                return available_slots
        
        except Exception as e:
            self.logger.error(f"Slot availability error: {e}")
            return ["10:00"]  # Default fallback
    
    async def _generate_appointment_confirmation(self, appointment: Dict[str, Any]) -> bytes:
        """Generate audio confirmation for site visit"""
        
        confirmation_script = f"""
        Perfect! I've scheduled your site visit for {appointment['scheduled_date']} at {appointment['scheduled_time']}.
        
        Our {appointment['staff_assigned']} will meet you at the property location.
        The visit will include {', '.join(appointment['visit_includes'][:3])} and will take approximately {appointment['duration']}.
        
        I'll send you the exact location details and contact numbers on WhatsApp.
        Please carry a valid ID for entry, and feel free to bring your family members.
        
        Is there anything specific you'd like to focus on during the visit?
        """
        
        return self.tts_service.create_industry_response(
            confirmation_script.strip(), 
            "real_estate"
        )
    
    def send_appointment_reminder(self, appointment_id: str, hours_before: int = 24) -> Dict[str, Any]:
        """Send appointment reminder call"""
        try:
            if appointment_id not in self.scheduled_appointments:
                return {"status": "error", "message": "Appointment not found"}
            
            appointment = self.scheduled_appointments[appointment_id]
            
            reminder_script = f"""
            Hello {appointment['lead_info'].get('name', '')}!
            
            This is a reminder about your property site visit tomorrow at {appointment['scheduled_time']}.
            The property is {appointment.get('property_name', 'our featured property')} 
            and our consultant {appointment.get('consultant_name', 'will be')} waiting for you.
            
            Please confirm if you're still available, or if you need to reschedule.
            For any queries, you can reach us at our dedicated number.
            
            Looking forward to showing you this amazing property!
            """
            
            reminder_audio = self.tts_service.create_industry_response(
                reminder_script.strip(),
                "real_estate"
            )
            
            # Mark reminder as sent
            appointment["reminder_scheduled"] = True
            appointment["reminder_sent_at"] = datetime.now().isoformat()
            
            return {
                "status": "success",
                "appointment_id": appointment_id,
                "reminder_audio": reminder_audio,
                "reminder_sent_at": appointment["reminder_sent_at"]
            }
        
        except Exception as e:
            self.logger.error(f"Reminder sending error: {e}")
            return {"status": "error", "message": str(e)}
    
    def reschedule_appointment(self, appointment_id: str, new_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Handle appointment rescheduling"""
        try:
            if appointment_id not in self.scheduled_appointments:
                return {"status": "error", "message": "Appointment not found"}
            
            appointment = self.scheduled_appointments[appointment_id]
            
            # Update appointment details
            appointment["scheduled_date"] = new_preferences.get("new_date", appointment["scheduled_date"])
            appointment["scheduled_time"] = new_preferences.get("new_time", appointment["scheduled_time"])
            appointment["rescheduled_at"] = datetime.now().isoformat()
            appointment["reschedule_reason"] = new_preferences.get("reason", "Customer request")
            
            # Generate rescheduling confirmation
            reschedule_script = f"""
            No problem at all! I've rescheduled your site visit to {appointment['scheduled_date']} at {appointment['scheduled_time']}.
            
            Your new appointment details have been updated, and I'll send you the confirmation on WhatsApp.
            
            Our consultant will be ready to meet you at the new time. 
            Thank you for letting us know in advance.
            """
            
            reschedule_audio = self.tts_service.create_industry_response(
                reschedule_script.strip(),
                "real_estate"
            )
            
            return {
                "status": "success",
                "appointment_id": appointment_id,
                "updated_appointment": appointment,
                "reschedule_confirmation_audio": reschedule_audio
            }
        
        except Exception as e:
            self.logger.error(f"Rescheduling error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_appointment_details(self, appointment_id: str) -> Dict[str, Any]:
        """Get appointment details"""
        if appointment_id in self.scheduled_appointments:
            return self.scheduled_appointments[appointment_id]
        return {"error": "Appointment not found"}
    
    def list_appointments(self, date_range: Optional[Dict[str, str]] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List appointments with optional filters"""
        try:
            appointments = list(self.scheduled_appointments.values())
            
            # Filter by date range if provided
            if date_range:
                start_date = datetime.strptime(date_range["start_date"], "%Y-%m-%d")
                end_date = datetime.strptime(date_range["end_date"], "%Y-%m-%d")
                
                filtered_appointments = []
                for apt in appointments:
                    apt_date = datetime.strptime(apt["scheduled_date"], "%Y-%m-%d")
                    if start_date <= apt_date <= end_date:
                        filtered_appointments.append(apt)
                appointments = filtered_appointments
            
            # Filter by status if provided
            if status:
                appointments = [apt for apt in appointments if apt["appointment_status"] == status]
            
            return appointments
        
        except Exception as e:
            self.logger.error(f"Appointment listing error: {e}")
            return []
    
    def cancel_appointment(self, appointment_id: str, reason: str) -> Dict[str, Any]:
        """Cancel appointment with audio confirmation"""
        try:
            if appointment_id not in self.scheduled_appointments:
                return {"status": "error", "message": "Appointment not found"}
            
            appointment = self.scheduled_appointments[appointment_id]
            
            # Update appointment status
            appointment["appointment_status"] = "cancelled"
            appointment["cancelled_at"] = datetime.now().isoformat()
            appointment["cancellation_reason"] = reason
            
            # Generate cancellation message
            cancellation_script = f"""
            I understand you need to cancel your site visit scheduled for {appointment['scheduled_date']}.
            No worries at all - your appointment has been cancelled.
            
            Please feel free to reschedule whenever you're ready. 
            I'll keep your property preferences on file and can arrange a visit at your convenience.
            
            Thank you for informing us in advance.
            """
            
            cancellation_audio = self.tts_service.create_industry_response(
                cancellation_script.strip(),
                "real_estate"
            )
            
            return {
                "status": "success",
                "appointment_id": appointment_id,
                "cancellation_confirmation_audio": cancellation_audio,
                "message": "Appointment cancelled successfully"
            }
        
        except Exception as e:
            self.logger.error(f"Appointment cancellation error: {e}")
            return {"status": "error", "message": str(e)}
