import asyncio
import logging
import json
from typing import Dict, Any
from datetime import datetime

class MockCRMService:
    """Mock CRM service - test without Salesforce complexity!"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data = {
            "contacts": [],
            "leads": [], 
            "tasks": [],
            "opportunities": []
        }
        
    async def initialize(self) -> bool:
        self.logger.info("Mock CRM initialized - No Salesforce setup needed!")
        return True
    
    async def sync_sales_call_data(self, call_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        contact_id = f"CONTACT_{len(self.data['contacts']) + 1}"
        
        # Store the call data
        contact = {
            "id": contact_id,
            "name": call_data.get("name", "Unknown Contact"),
            "phone": call_data.get("phone", ""),
            "call_analysis": analysis,
            "created_at": datetime.now().isoformat()
        }
        
        self.data["contacts"].append(contact)
        
        # Create a task for the call
        task = {
            "id": f"TASK_{len(self.data['tasks']) + 1}",
            "contact_id": contact_id,
            "subject": "AI-Powered Sales Call",
            "description": f"Engagement Score: {analysis.get('engagement_score', 'N/A')}/10",
            "status": "Completed",
            "created_at": datetime.now().isoformat()
        }
        
        self.data["tasks"].append(task)
        
        self.logger.info(f"Sales call synced: {contact_id}")
        
        return {
            "status": "success",
            "contact_id": contact_id,
            "task_id": task["id"],
            "sync_time_seconds": 0.1,
            "message": "Successfully synced to Mock CRM!"
        }
    
    async def sync_real_estate_lead(self, lead_data: Dict[str, Any], qualification_data: Dict[str, Any]) -> Dict[str, Any]:
        lead_id = f"LEAD_{len(self.data['leads']) + 1}"
        
        # Store the lead
        lead = {
            "id": lead_id,
            "name": lead_data.get("name", "Unknown Lead"),
            "phone": lead_data.get("phone", ""),
            "qualification_score": qualification_data.get("qualification_score", 0),
            "budget_range": qualification_data.get("budget_range", "Not disclosed"),
            "property_type": qualification_data.get("property_type", ""),
            "locations": qualification_data.get("locations", []),
            "timeline": qualification_data.get("timeline", ""),
            "created_at": datetime.now().isoformat()
        }
        
        self.data["leads"].append(lead)
        
        self.logger.info(f"Real estate lead synced: {lead_id}")
        
        return {
            "status": "success",
            "lead_id": lead_id,
            "qualification_score": lead["qualification_score"],
            "sync_time_seconds": 0.1,
            "message": f"Lead qualified with score {lead['qualification_score']}/10!"
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        return {
            "status": "success",
            "message": "Mock CRM connection is active!",
            "data_summary": {
                "total_contacts": len(self.data["contacts"]),
                "total_leads": len(self.data["leads"]),
                "total_tasks": len(self.data["tasks"])
            }
        }
    
    async def get_sync_statistics(self) -> Dict[str, Any]:
        total_syncs = len(self.data["contacts"]) + len(self.data["leads"])
        
        return {
            "total_syncs": total_syncs,
            "successful_syncs": total_syncs,
            "failed_syncs": 0,
            "success_rate": "100.0%",
            "avg_sync_time": "0.10s",
            "connection_status": "Connected (Mock CRM)",
            "last_sync": datetime.now().isoformat() if total_syncs > 0 else None
        }
    
    def get_all_data(self) -> Dict[str, Any]:
        """Debug function to see all stored data"""
        return self.data
