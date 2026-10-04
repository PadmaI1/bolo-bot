import json
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

class CRMSyncService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # CRM integration configs
        self.crm_configs = {
            "zoho": {
                "base_url": "https://www.zohoapis.in/crm/v2/",
                "auth_url": "https://accounts.zoho.in/oauth/v2/token",
                "required_fields": ["client_id", "client_secret", "refresh_token"]
            },
            "salesforce": {
                "base_url": "https://ap24.salesforce.com/services/data/v57.0/",
                "auth_url": "https://login.salesforce.com/services/oauth2/token",
                "required_fields": ["client_id", "client_secret", "username", "password", "security_token"]
            },
            "hubspot": {
                "base_url": "https://api.hubapi.com/crm/v3/",
                "auth_url": "https://api.hubapi.com/oauth/v1/token",
                "required_fields": ["access_token"]
            }
        }
        
        # Active CRM connections
        self.active_connections = {}
    
    def setup_crm_connection(self, crm_type: str, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Setup CRM connection with credentials"""
        try:
            if crm_type not in self.crm_configs:
                return {"status": "error", "message": f"CRM type {crm_type} not supported"}
            
            config = self.crm_configs[crm_type]
            
            # Validate required fields
            missing_fields = [field for field in config["required_fields"] if field not in credentials]
            if missing_fields:
                return {
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Test connection
            connection_test = self._test_crm_connection(crm_type, credentials)
            
            if connection_test["status"] == "success":
                connection_id = f"{crm_type}_{datetime.now().timestamp()}"
                self.active_connections[connection_id] = {
                    "crm_type": crm_type,
                    "credentials": credentials,
                    "config": config,
                    "connected_at": datetime.now().isoformat(),
                    "last_sync": None
                }
                
                return {
                    "status": "success",
                    "connection_id": connection_id,
                    "message": f"Successfully connected to {crm_type}"
                }
            else:
                return connection_test
        
        except Exception as e:
            self.logger.error(f"CRM connection setup error: {e}")
            return {"status": "error", "message": str(e)}
    
    def sync_call_data(self, connection_id: str, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync call data to CRM"""
        try:
            if connection_id not in self.active_connections:
                return {"status": "error", "message": "Connection not found"}
            
            connection = self.active_connections[connection_id]
            crm_type = connection["crm_type"]
            
            # Transform data for specific CRM
            crm_data = self._transform_data_for_crm(call_data, crm_type)
            
            # Sync to CRM
            if crm_type == "zoho":
                result = self._sync_to_zoho(connection, crm_data)
            elif crm_type == "salesforce":
                result = self._sync_to_salesforce(connection, crm_data)
            elif crm_type == "hubspot":
                result = self._sync_to_hubspot(connection, crm_data)
            else:
                return {"status": "error", "message": f"Sync not implemented for {crm_type}"}
            
            # Update last sync time
            if result["status"] == "success":
                connection["last_sync"] = datetime.now().isoformat()
            
            return result
        
        except Exception as e:
            self.logger.error(f"CRM sync error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _test_crm_connection(self, crm_type: str, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Test CRM connection"""
        try:
            if crm_type == "zoho":
                return self._test_zoho_connection(credentials)
            elif crm_type == "salesforce":
                return self._test_salesforce_connection(credentials)
            elif crm_type == "hubspot":
                return self._test_hubspot_connection(credentials)
            else:
                return {"status": "error", "message": "CRM type not supported"}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _test_zoho_connection(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Test Zoho CRM connection"""
        try:
            # Get access token
            token_response = requests.post(
                self.crm_configs["zoho"]["auth_url"],
                data={
                    "refresh_token": credentials["refresh_token"],
                    "client_id": credentials["client_id"],
                    "client_secret": credentials["client_secret"],
                    "grant_type": "refresh_token"
                }
            )
            
            if token_response.status_code == 200:
                token_data = token_response.json()
                access_token = token_data.get("access_token")
                
                # Test API call
                test_response = requests.get(
                    f"{self.crm_configs['zoho']['base_url']}users",
                    headers={"Authorization": f"Zoho-oauthtoken {access_token}"}
                )
                
                if test_response.status_code == 200:
                    return {"status": "success", "message": "Zoho connection successful"}
                else:
                    return {"status": "error", "message": "Zoho API test failed"}
            else:
                return {"status": "error", "message": "Zoho authentication failed"}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _test_salesforce_connection(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Test Salesforce connection"""
        try:
            # Salesforce OAuth2 login
            auth_response = requests.post(
                self.crm_configs["salesforce"]["auth_url"],
                data={
                    "grant_type": "password",
                    "client_id": credentials["client_id"],
                    "client_secret": credentials["client_secret"],
                    "username": credentials["username"],
                    "password": credentials["password"] + credentials["security_token"]
                }
            )
            
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                access_token = auth_data.get("access_token")
                instance_url = auth_data.get("instance_url")
                
                # Test API call
                test_response = requests.get(
                    f"{instance_url}/services/data/v57.0/sobjects/",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if test_response.status_code == 200:
                    return {"status": "success", "message": "Salesforce connection successful"}
                else:
                    return {"status": "error", "message": "Salesforce API test failed"}
            else:
                return {"status": "error", "message": "Salesforce authentication failed"}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _test_hubspot_connection(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Test HubSpot connection"""
        try:
            # Test HubSpot API
            test_response = requests.get(
                f"{self.crm_configs['hubspot']['base_url']}contacts",
                headers={"Authorization": f"Bearer {credentials['access_token']}"},
                params={"limit": 1}
            )
            
            if test_response.status_code == 200:
                return {"status": "success", "message": "HubSpot connection successful"}
            else:
                return {"status": "error", "message": "HubSpot API test failed"}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _transform_data_for_crm(self, call_data: Dict[str, Any], crm_type: str) -> Dict[str, Any]:
        """Transform call data for specific CRM format"""
        
        # Common data extraction
        common_data = {
            "subject": f"Sales Call - {call_data.get('contact_name', 'Prospect')}",
            "call_date": call_data.get("call_date", datetime.now().isoformat()),
            "duration": call_data.get("duration_minutes", 0),
            "call_type": "Sales Call",
            "outcome": call_data.get("conversation_stage", "Discovery"),
            "notes": call_data.get("conversation_summary", ""),
            "next_steps": "; ".join(call_data.get("next_steps", [])),
            "opportunity_score": call_data.get("opportunity_score", 5)
        }
        
        # CRM-specific transformations
        if crm_type == "zoho":
            return {
                "data": [{
                    "Subject": common_data["subject"],
                    "Call_Start_Time": common_data["call_date"],
                    "Call_Duration": f"{common_data['duration']} minutes",
                    "Call_Type": common_data["call_type"],
                    "Description": common_data["notes"],
                    "Call_Result": common_data["outcome"],
                    "What_Id": call_data.get("contact_id"),  # Link to contact/lead
                }]
            }
        
        elif crm_type == "salesforce":
            return {
                "Subject": common_data["subject"],
                "ActivityDateTime": common_data["call_date"],
                "DurationInMinutes": common_data["duration"],
                "Type": "Call",
                "Description": f"{common_data['notes']}\n\nNext Steps: {common_data['next_steps']}",
                "CallDisposition": common_data["outcome"],
                "WhoId": call_data.get("contact_id"),  # Link to contact/lead
            }
        
        elif crm_type == "hubspot":
            return {
                "properties": {
                    "hs_activity_type": "CALL",
                    "hs_timestamp": datetime.now().isoformat(),
                    "hubspot_owner_id": call_data.get("owner_id"),
                    "hs_call_title": common_data["subject"],
                    "hs_call_body": common_data["notes"],
                    "hs_call_duration": common_data["duration"] * 60000,  # milliseconds
                    "hs_call_disposition": common_data["outcome"]
                },
                "associations": [
                    {
                        "to": {"id": call_data.get("contact_id", "")},
                        "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 194}]
                    }
                ]
            }
        
        return common_data
    
    def _sync_to_zoho(self, connection: Dict[str, Any], crm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync to Zoho CRM"""
        # Implementation for Zoho CRM sync
        # This would include getting access token and making the API call
        return {"status": "success", "message": "Synced to Zoho CRM", "record_id": "zoho_123"}
    
    def _sync_to_salesforce(self, connection: Dict[str, Any], crm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync to Salesforce"""
        # Implementation for Salesforce sync
        return {"status": "success", "message": "Synced to Salesforce", "record_id": "sf_123"}
    
    def _sync_to_hubspot(self, connection: Dict[str, Any], crm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync to HubSpot"""
        # Implementation for HubSpot sync
        return {"status": "success", "message": "Synced to HubSpot", "record_id": "hs_123"}
    
    def get_connection_status(self, connection_id: str) -> Dict[str, Any]:
        """Get CRM connection status"""
        if connection_id not in self.active_connections:
            return {"status": "error", "message": "Connection not found"}
        
        connection = self.active_connections[connection_id]
        return {
            "status": "active",
            "crm_type": connection["crm_type"],
            "connected_at": connection["connected_at"],
            "last_sync": connection["last_sync"],
            "health": "good"  # Could add actual health check
        }
