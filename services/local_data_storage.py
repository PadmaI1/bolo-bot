"""
Local Data Storage - Store call records in JSON files
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class LocalDataStorage:
    """Manages local storage of call records in JSON files"""
    
    def __init__(self, storage_dir: str = "database"):
        self.storage_dir = storage_dir
        self.b2b_file = os.path.join(storage_dir, "b2b_sales_records.json")
        self.realestate_file = os.path.join(storage_dir, "real_estate_records.json")
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()
        
        logger.info(f"✅ Local storage initialized - Directory: {storage_dir}")
    
    def _initialize_files(self):
        """Initialize storage files with empty data if they don't exist"""
        files = [
            (self.b2b_file, {"calls": [], "metadata": {"total_calls": 0, "last_updated": ""}}),
            (self.realestate_file, {"calls": [], "metadata": {"total_calls": 0, "last_updated": ""}})
        ]
        
        for file_path, initial_data in files:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, indent=2, ensure_ascii=False)
                logger.info(f"✅ Created storage file: {file_path}")
    
    def save_call_record(self, call_type: str, call_record: Dict[str, Any]) -> bool:
        """Save call record to appropriate file"""
        try:
            # Determine which file to use
            file_path = self.b2b_file if call_type == "b2b_sales" else self.realestate_file
            
            # Load existing data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Add timestamp if not present
            if "saved_at" not in call_record:
                call_record["saved_at"] = datetime.now().isoformat()
            
            # Check if call already exists (update) or new (append)
            call_sid = call_record.get("call_sid", "")
            existing_index = None
            
            for i, existing_call in enumerate(data["calls"]):
                if existing_call.get("call_sid") == call_sid:
                    existing_index = i
                    break
            
            if existing_index is not None:
                # Update existing record
                data["calls"][existing_index] = call_record
                logger.info(f"📝 Updated {call_type} call record: {call_sid}")
            else:
                # Add new record at the beginning (most recent first)
                data["calls"].insert(0, call_record)
                data["metadata"]["total_calls"] = len(data["calls"])
                logger.info(f"📝 Saved new {call_type} call record: {call_sid}")
            
            # Update metadata
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Save back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save call record: {e}")
            return False
    
    def get_call_records(self, call_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get call records from appropriate file"""
        try:
            file_path = self.b2b_file if call_type == "b2b_sales" else self.realestate_file
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            calls = data.get("calls", [])
            
            # Already sorted (most recent first from insert)
            return calls[:limit]
            
        except Exception as e:
            logger.error(f"❌ Failed to load call records: {e}")
            return []
    
    def get_dashboard_stats(self, call_type: str) -> Dict[str, Any]:
        """Get statistics for dashboard display"""
        try:
            calls = self.get_call_records(call_type=call_type, limit=1000)
            
            if not calls:
                return {
                    "total_calls": 0,
                    "avg_duration": 0,
                    "avg_lead_score": 0,
                    "high_quality_leads": 0,
                    "recent_calls": []
                }
            
            # Calculate statistics
            total_calls = len(calls)
            total_duration = sum(call.get("duration_seconds", 0) for call in calls)
            avg_duration = total_duration // total_calls if total_calls > 0 else 0
            
            lead_scores = [call.get("lead_score", 0) for call in calls if call.get("lead_score")]
            avg_lead_score = sum(lead_scores) // len(lead_scores) if lead_scores else 0
            
            # High quality leads (score > 6)
            high_quality_leads = len([score for score in lead_scores if score > 6])
            
            return {
                "total_calls": total_calls,
                "avg_duration": avg_duration,
                "avg_lead_score": avg_lead_score,
                "high_quality_leads": high_quality_leads,
                "recent_calls": calls[:10]  # Last 10 calls
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate dashboard stats: {e}")
            return {"error": str(e)}
    
    def clear_records(self, call_type: str) -> bool:
        """Clear all records for a call type (for testing)"""
        try:
            file_path = self.b2b_file if call_type == "b2b_sales" else self.realestate_file
            
            data = {"calls": [], "metadata": {"total_calls": 0, "last_updated": datetime.now().isoformat()}}
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Cleared {call_type} records")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear records: {e}")
            return False

# Global instance
storage = LocalDataStorage()
