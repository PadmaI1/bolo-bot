import asyncio
import logging
import json
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceError
import os
from dotenv import load_dotenv

load_dotenv()

class SalesforceIntegration:
    """Production-ready Salesforce CRM integration for BoloBot AI Platform"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Salesforce credentials
        self.username = os.getenv("SALESFORCE_USERNAME")
        self.password = os.getenv("SALESFORCE_PASSWORD")
        self.security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")
        self.client_id = os.getenv("SALESFORCE_CLIENT_ID")
        self.client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
        self.domain = os.getenv("SALESFORCE_DOMAIN", "login")
        
        # Salesforce connection
        self.sf = None
        self.session = None
        self.last_connection_test = None
        
        # Field mappings for different industries
        self.field_mappings = {
            "sales": {
                "lead_fields": [
                    "FirstName", "LastName", "Company", "Phone", "Email",
                    "LeadSource", "Status", "Rating", "Industry", "Title"
                ],
                "opportunity_fields": [
                    "Name", "AccountId", "Amount", "StageName", "CloseDate",
                    "Probability", "LeadSource", "Type", "Description"
                ],
                "contact_fields": [
                    "FirstName", "LastName", "Phone", "Email", "Title",
                    "AccountId", "LeadSource", "Department"
                ],
                "task_fields": [
                    "Subject", "Description", "Status", "Priority", "ActivityDate",
                    "WhoId", "WhatId", "Type", "CallDurationInSeconds"
                ]
            },
            "real_estate": {
                "lead_fields": [
                    "FirstName", "LastName", "Phone", "Email", "LeadSource",
                    "Status", "Rating", "Budget__c", "Property_Type__c", 
                    "Preferred_Location__c", "Timeline__c", "Financing_Status__c"
                ],
                "custom_objects": {
                    "Property_Inquiry__c": [
                        "Lead__c", "Property_Type__c", "Budget_Range__c",
                        "Location_Preference__c", "Timeline__c", "Status__c",
                        "Qualification_Score__c", "Next_Action__c"
                    ],
                    "Site_Visit__c": [
                        "Lead__c", "Property__c", "Scheduled_Date__c",
                        "Visit_Type__c", "Status__c", "Outcome__c", "Notes__c"
                    ]
                }
            }
        }
        
        # Integration statistics
        self.sync_stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "last_sync_time": None,
            "avg_sync_time": 0
        }
    
    async def initialize(self) -> bool:
        """Initialize Salesforce connection and validate credentials"""
        try:
            self.logger.info("Initializing Salesforce connection...")
            
            # Create Salesforce connection
            self.sf = Salesforce(
                username=self.username,
                password=self.password,
                security_token=self.security_token,
                client_id=self.client_id,
                domain=self.domain
            )
            
            # Test connection
            user_info = self.sf.query("SELECT Id, Name, Email FROM User WHERE Id = '{}'".format(self.sf.sf_session.user_id))
            
            if user_info["records"]:
                self.logger.info(f"Salesforce connection successful. User: {user_info['records'][0]['Name']}")
                self.last_connection_test = datetime.now()
                return True
            else:
                self.logger.error("Failed to retrieve user information from Salesforce")
                return False
                
        except Exception as e:
            self.logger.error(f"Salesforce initialization failed: {e}")
            return False
    
    async def sync_sales_call_data(self, call_data: Dict[str, Any], session_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Sync sales call data to Salesforce"""
        start_time = datetime.now()
        
        try:
            if not self.sf:
                await self.initialize()
            
            # Prepare lead/contact information
            contact_info = self._extract_contact_info(call_data)
            
            # Find or create lead/contact
            salesforce_contact = await self._find_or_create_contact(contact_info, "sales")
            
            if not salesforce_contact:
                return {"status": "error", "message": "Failed to create/find contact"}
            
            # Create call activity task
            call_task = await self._create_call_task(salesforce_contact["Id"], call_data, session_analysis)
            
            # Update opportunity if exists or create new one
            opportunity_result = await self._update_or_create_opportunity(salesforce_contact, session_analysis)
            
            # Update lead scoring and next actions
            await self._update_lead_scoring(salesforce_contact["Id"], session_analysis)
            
            # Track sync performance
            sync_time = (datetime.now() - start_time).total_seconds()
            self._update_sync_stats(True, sync_time)
            
            return {
                "status": "success",
                "contact_id": salesforce_contact["Id"],
                "task_id": call_task.get("id") if call_task else None,
                "opportunity_id": opportunity_result.get("id") if opportunity_result else None,
                "sync_time_seconds": sync_time
            }
            
        except Exception as e:
            self.logger.error(f"Sales call sync error: {e}")
            self._update_sync_stats(False, (datetime.now() - start_time).total_seconds())
            return {"status": "error", "message": str(e)}
    
    async def sync_real_estate_lead(self, lead_data: Dict[str, Any], qualification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync real estate lead qualification data to Salesforce"""
        start_time = datetime.now()
        
        try:
            if not self.sf:
                await self.initialize()
            
            # Extract lead information
            contact_info = self._extract_contact_info(lead_data)
            
            # Find or create lead
            salesforce_lead = await self._find_or_create_contact(contact_info, "real_estate")
            
            if not salesforce_lead:
                return {"status": "error", "message": "Failed to create/find lead"}
            
            # Create property inquiry record
            property_inquiry = await self._create_property_inquiry(salesforce_lead["Id"], qualification_data)
            
            # Schedule site visit if qualified
            site_visit_result = None
            if qualification_data.get("qualification_score", 0) >= 7:
                site_visit_result = await self._create_site_visit_record(salesforce_lead["Id"], qualification_data)
            
            # Update lead with qualification data
            await self._update_lead_qualification(salesforce_lead["Id"], qualification_data)
            
            # Track performance
            sync_time = (datetime.now() - start_time).total_seconds()
            self._update_sync_stats(True, sync_time)
            
            return {
                "status": "success",
                "lead_id": salesforce_lead["Id"],
                "property_inquiry_id": property_inquiry.get("id") if property_inquiry else None,
                "site_visit_id": site_visit_result.get("id") if site_visit_result else None,
                "sync_time_seconds": sync_time
            }
            
        except Exception as e:
            self.logger.error(f"Real estate lead sync error: {e}")
            self._update_sync_stats(False, (datetime.now() - start_time).total_seconds())
            return {"status": "error", "message": str(e)}
    
    def _extract_contact_info(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract contact information from call/lead data"""
        return {
            "FirstName": data.get("first_name", data.get("name", "").split()[0] if data.get("name") else "Unknown"),
            "LastName": data.get("last_name", " ".join(data.get("name", "").split()[1:]) if data.get("name") else "Contact"),
            "Phone": data.get("phone", data.get("mobile", "")),
            "Email": data.get("email", ""),
            "Company": data.get("company", data.get("organization", "")),
            "Title": data.get("title", data.get("designation", "")),
            "LeadSource": "BoloBot AI Platform"
        }
    
    async def _find_or_create_contact(self, contact_info: Dict[str, str], industry: str) -> Optional[Dict[str, Any]]:
        """Find existing contact or create new one"""
        try:
            # Search by phone or email
            search_queries = []
            if contact_info.get("Phone"):
                search_queries.append(f"Phone = '{contact_info['Phone']}'")
            if contact_info.get("Email"):
                search_queries.append(f"Email = '{contact_info['Email']}'")
            
            if not search_queries:
                # Create new contact if no search criteria
                return await self._create_new_contact(contact_info, industry)
            
            # Check for existing contact/lead
            if industry == "sales":
                # Check contacts first, then leads
                for obj_type in ["Contact", "Lead"]:
                    for query in search_queries:
                        soql = f"SELECT Id, FirstName, LastName, Phone, Email FROM {obj_type} WHERE {query} LIMIT 1"
                        result = self.sf.query(soql)
                        
                        if result["records"]:
                            self.logger.info(f"Found existing {obj_type}: {result['records'][0]['Id']}")
                            return result["records"][0]
            
            else:  # real_estate
                # Check leads for real estate
                for query in search_queries:
                    soql = f"SELECT Id, FirstName, LastName, Phone, Email FROM Lead WHERE {query} LIMIT 1"
                    result = self.sf.query(soql)
                    
                    if result["records"]:
                        self.logger.info(f"Found existing lead: {result['records'][0]['Id']}")
                        return result["records"][0]
            
            # No existing contact found, create new one
            return await self._create_new_contact(contact_info, industry)
            
        except Exception as e:
            self.logger.error(f"Contact search/creation error: {e}")
            return None
    
    async def _create_new_contact(self, contact_info: Dict[str, str], industry: str) -> Optional[Dict[str, Any]]:
        """Create new contact/lead in Salesforce"""
        try:
            # Choose object type based on industry
            if industry == "sales":
                # Create as Lead first (standard B2B process)
                object_type = "Lead"
                contact_info["Status"] = "Open - Not Contacted"
                contact_info["Rating"] = "Warm"  # From AI qualification
            else:
                # Real estate leads
                object_type = "Lead"
                contact_info["Status"] = "Open - Not Contacted"
                contact_info["Industry"] = "Real Estate"
            
            # Create the record
            result = getattr(self.sf, object_type).create(contact_info)
            
            if result.get("success"):
                self.logger.info(f"Created new {object_type}: {result['id']}")
                
                # Return the created record with ID
                contact_info["Id"] = result["id"]
                return contact_info
            else:
                self.logger.error(f"Failed to create {object_type}: {result}")
                return None
                
        except Exception as e:
            self.logger.error(f"Contact creation error: {e}")
            return None
    
    async def _create_call_task(self, contact_id: str, call_data: Dict[str, Any], analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create call activity task in Salesforce"""
        try:
            # Extract call details
            call_duration = call_data.get("duration_minutes", 0) * 60  # Convert to seconds
            call_summary = self._generate_call_summary(analysis)
            
            task_data = {
                "Subject": f"AI-Assisted Sales Call - {datetime.now().strftime('%Y-%m-%d')}",
                "Description": call_summary,
                "Status": "Completed",
                "Priority": "Normal",
                "Type": "Call",
                "WhoId": contact_id,
                "ActivityDate": datetime.now().strftime("%Y-%m-%d"),
                "CallDurationInSeconds": int(call_duration),
                "CallType": "Outbound"  # Assuming outbound for demo
            }
            
            # Add coaching insights if available
            if analysis.get("coaching_metrics"):
                metrics = analysis["coaching_metrics"]
                task_data["Description"] += f"\n\nAI Coaching Metrics:\n"
                task_data["Description"] += f"- Questions Asked: {metrics.get('questions_asked', 0)}\n"
                task_data["Description"] += f"- Buying Signals: {metrics.get('buying_signals', 0)}\n"
                task_data["Description"] += f"- Engagement Score: {metrics.get('engagement_score', 0)}/10"
            
            result = self.sf.Task.create(task_data)
            
            if result.get("success"):
                self.logger.info(f"Created call task: {result['id']}")
                return result
            else:
                self.logger.error(f"Failed to create call task: {result}")
                return None
                
        except Exception as e:
            self.logger.error(f"Call task creation error: {e}")
            return None
    
    async def _update_or_create_opportunity(self, contact: Dict[str, Any], analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing opportunity or create new one based on analysis"""
        try:
            # Check if opportunity already exists for this contact
            contact_id = contact["Id"]
            
            # Search for existing opportunities
            soql = f"SELECT Id, Name, StageName, Amount FROM Opportunity WHERE ContactId = '{contact_id}' OR AccountId IN (SELECT AccountId FROM Contact WHERE Id = '{contact_id}') ORDER BY CreatedDate DESC LIMIT 1"
            
            try:
                result = self.sf.query(soql)
                existing_opp = result["records"][0] if result["records"] else None
            except:
                existing_opp = None
            
            # Determine deal stage from analysis
            deal_stage = self._map_analysis_to_stage(analysis)
            opportunity_amount = self._estimate_deal_size(analysis)
            
            if existing_opp:
                # Update existing opportunity
                update_data = {
                    "StageName": deal_stage,
                    "LastModifiedDate": datetime.now().isoformat(),
                    "Description": f"Updated via AI analysis on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                }
                
                if opportunity_amount:
                    update_data["Amount"] = opportunity_amount
                
                result = self.sf.Opportunity.update(existing_opp["Id"], update_data)
                return {"id": existing_opp["Id"], "updated": True}
                
            else:
                # Create new opportunity
                opp_data = {
                    "Name": f"{contact.get('FirstName', '')} {contact.get('LastName', '')} - AI Generated",
                    "StageName": deal_stage,
                    "CloseDate": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),  # 30 days from now
                    "LeadSource": "BoloBot AI Platform",
                    "Type": "New Customer",
                    "Description": f"Opportunity created from AI voice analysis on {datetime.now().strftime('%Y-%m-%d')}"
                }
                
                if opportunity_amount:
                    opp_data["Amount"] = opportunity_amount
                
                # Try to link to contact's account
                if contact.get("AccountId"):
                    opp_data["AccountId"] = contact["AccountId"]
                
                result = self.sf.Opportunity.create(opp_data)
                
                if result.get("success"):
                    return {"id": result["id"], "created": True}
                
            return None
            
        except Exception as e:
            self.logger.error(f"Opportunity update/creation error: {e}")
            return None
    
    async def _create_property_inquiry(self, lead_id: str, qualification_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create property inquiry custom object record"""
        try:
            inquiry_data = {
                "Lead__c": lead_id,
                "Property_Type__c": qualification_data.get("property_type", "").title(),
                "Budget_Range__c": qualification_data.get("budget_range", "Not Disclosed"),
                "Location_Preference__c": ", ".join(qualification_data.get("locations", [])),
                "Timeline__c": qualification_data.get("timeline", "Exploring").title(),
                "Status__c": "Active",
                "Qualification_Score__c": qualification_data.get("qualification_score", 0),
                "Next_Action__c": self._determine_next_action(qualification_data),
                "Created_Date__c": datetime.now().isoformat(),
                "Source__c": "BoloBot AI Platform"
            }
            
            # Add financing information if available
            if qualification_data.get("financing_status"):
                inquiry_data["Financing_Status__c"] = qualification_data["financing_status"].title()
            
            result = self.sf.Property_Inquiry__c.create(inquiry_data)
            
            if result.get("success"):
                self.logger.info(f"Created property inquiry: {result['id']}")
                return result
            else:
                self.logger.error(f"Failed to create property inquiry: {result}")
                return None
                
        except Exception as e:
            self.logger.error(f"Property inquiry creation error: {e}")
            return None
    
    async def _create_site_visit_record(self, lead_id: str, qualification_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create site visit record for qualified leads"""
        try:
            # Determine visit type based on qualification
            visit_type = "Individual Visit"
            if qualification_data.get("family_involvement") in ["joint_family_decision", "spouse"]:
                visit_type = "Group Visit"
            elif qualification_data.get("buyer_type") == "investor":
                visit_type = "Investor Briefing"
            
            # Schedule for next available weekend
            today = datetime.now()
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0 and today.hour > 17:  # If it's Saturday evening, schedule next week
                days_until_saturday = 7
            
            visit_date = today + timedelta(days=days_until_saturday)
            
            visit_data = {
                "Lead__c": lead_id,
                "Scheduled_Date__c": visit_date.strftime("%Y-%m-%d"),
                "Visit_Type__c": visit_type,
                "Status__c": "Scheduled",
                "Created_Date__c": datetime.now().isoformat(),
                "Notes__c": f"Auto-scheduled based on qualification score: {qualification_data.get('qualification_score', 0)}/10"
            }
            
            result = self.sf.Site_Visit__c.create(visit_data)
            
            if result.get("success"):
                self.logger.info(f"Created site visit record: {result['id']}")
                return result
            else:
                self.logger.error(f"Failed to create site visit: {result}")
                return None
                
        except Exception as e:
            self.logger.error(f"Site visit creation error: {e}")
            return None
    
    def _generate_call_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate human-readable call summary"""
        summary_parts = ["AI-Powered Sales Call Summary:\n"]
        
        if analysis.get("conversation_stage"):
            summary_parts.append(f"Conversation Stage: {analysis['conversation_stage'].title()}")
        
        if analysis.get("sentiment"):
            sentiment = analysis["sentiment"]
            summary_parts.append(f"Customer Sentiment: {sentiment.get('customer_mood', 'neutral').title()}")
            summary_parts.append(f"Engagement Level: {sentiment.get('engagement_level', 'medium').title()}")
            
            if sentiment.get("buying_signals"):
                summary_parts.append(f"Buying Signals: {', '.join(sentiment['buying_signals'][:3])}")
        
        if analysis.get("deal_progression"):
            progression = analysis["deal_progression"]
            summary_parts.append(f"Deal Progression Score: {progression.get('progression_score', 'N/A')}/10")
            summary_parts.append(f"Next Best Action: {progression.get('next_best_action', 'Follow up')}")
        
        if analysis.get("objection_handling") and analysis["objection_handling"].get("objection_type") != "none":
            objection = analysis["objection_handling"]
            summary_parts.append(f"Objection Handled: {objection['objection_type'].title()}")
        
        return "\n".join(summary_parts)
    
    def _map_analysis_to_stage(self, analysis: Dict[str, Any]) -> str:
        """Map AI analysis to Salesforce opportunity stages"""
        conversation_stage = analysis.get("conversation_stage", "discovery")
        buying_signals = len(analysis.get("sentiment", {}).get("buying_signals", []))
        progression_score = analysis.get("deal_progression", {}).get("progression_score", 0)
        
        # Map to standard Salesforce stages
        if conversation_stage == "closing" or buying_signals >= 3:
            return "Negotiation/Review"
        elif conversation_stage == "presentation" or progression_score >= 7:
            return "Proposal/Price Quote"
        elif conversation_stage == "objection_handling":
            return "Needs Analysis"
        elif conversation_stage == "discovery":
            return "Prospecting"
        else:
            return "Qualification"
    
    def _estimate_deal_size(self, analysis: Dict[str, Any]) -> Optional[float]:
        """Estimate deal size based on conversation analysis"""
        # This would be more sophisticated in production
        # For demo, return a reasonable estimate based on engagement
        engagement_score = analysis.get("coaching_metrics", {}).get("engagement_score", 5.0)
        
        # Base deal size estimation (this would be industry-specific)
        if engagement_score >= 8:
            return 50000.0  # High engagement = larger deal potential
        elif engagement_score >= 6:
            return 25000.0  # Medium engagement
        elif engagement_score >= 4:
            return 10000.0  # Low engagement
        
        return None  # Don't estimate if very low engagement
    
    def _determine_next_action(self, qualification_data: Dict[str, Any]) -> str:
        """Determine next action based on qualification score"""
        score = qualification_data.get("qualification_score", 0)
        
        if score >= 8:
            return "Schedule Site Visit"
        elif score >= 6:
            return "Send Property Portfolio"
        elif score >= 4:
            return "Follow-up Call"
        else:
            return "Nurture Campaign"
    
    async def _update_lead_scoring(self, contact_id: str, analysis: Dict[str, Any]):
        """Update lead scoring based on AI analysis"""
        try:
            # Calculate lead score based on multiple factors
            base_score = 50  # Starting score
            
            # Adjust based on engagement
            engagement_score = analysis.get("coaching_metrics", {}).get("engagement_score", 5.0)
            score_adjustment = (engagement_score - 5) * 10  # +/- 50 points based on engagement
            
            # Adjust based on buying signals
            buying_signals = len(analysis.get("sentiment", {}).get("buying_signals", []))
            score_adjustment += buying_signals * 5
            
            # Adjust based on objections (negative impact)
            objection_severity = analysis.get("objection_handling", {}).get("objection_severity", "low")
            if objection_severity == "high":
                score_adjustment -= 20
            elif objection_severity == "medium":
                score_adjustment -= 10
            
            final_score = max(0, min(100, base_score + score_adjustment))  # Keep between 0-100
            
            # Update the lead/contact
            update_data = {
                "Rating": "Hot" if final_score >= 80 else "Warm" if final_score >= 60 else "Cold",
                "LastModifiedDate": datetime.now().isoformat()
            }
            
            # Try to update as Contact first, then Lead
            for obj_type in ["Contact", "Lead"]:
                try:
                    getattr(self.sf, obj_type).update(contact_id, update_data)
                    self.logger.info(f"Updated {obj_type} scoring: {contact_id} -> {final_score}")
                    break
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Lead scoring update error: {e}")
    
    async def _update_lead_qualification(self, lead_id: str, qualification_data: Dict[str, Any]):
        """Update lead with qualification data"""
        try:
            update_data = {
                "Status": "Qualified" if qualification_data.get("qualification_score", 0) >= 7 else "Working - Contacted",
                "Rating": "Hot" if qualification_data.get("qualification_score", 0) >= 8 else "Warm",
                "Budget__c": qualification_data.get("budget_range", ""),
                "Property_Type__c": qualification_data.get("property_type", ""),
                "Preferred_Location__c": ", ".join(qualification_data.get("locations", [])),
                "Timeline__c": qualification_data.get("timeline", ""),
                "Financing_Status__c": qualification_data.get("financing_status", ""),
                "LastModifiedDate": datetime.now().isoformat()
            }
            
            self.sf.Lead.update(lead_id, update_data)
            self.logger.info(f"Updated lead qualification: {lead_id}")
            
        except Exception as e:
            self.logger.error(f"Lead qualification update error: {e}")
    
    def _update_sync_stats(self, success: bool, sync_time: float):
        """Update synchronization statistics"""
        self.sync_stats["total_syncs"] += 1
        
        if success:
            self.sync_stats["successful_syncs"] += 1
        else:
            self.sync_stats["failed_syncs"] += 1
        
        # Update average sync time
        total_syncs = self.sync_stats["total_syncs"]
        current_avg = self.sync_stats["avg_sync_time"]
        self.sync_stats["avg_sync_time"] = (current_avg * (total_syncs - 1) + sync_time) / total_syncs
        self.sync_stats["last_sync_time"] = datetime.now().isoformat()
    
    async def get_sync_statistics(self) -> Dict[str, Any]:
        """Get synchronization performance statistics"""
        success_rate = 0
        if self.sync_stats["total_syncs"] > 0:
            success_rate = (self.sync_stats["successful_syncs"] / self.sync_stats["total_syncs"]) * 100
        
        return {
            "total_syncs": self.sync_stats["total_syncs"],
            "successful_syncs": self.sync_stats["successful_syncs"],
            "failed_syncs": self.sync_stats["failed_syncs"],
            "success_rate": f"{success_rate:.1f}%",
            "avg_sync_time": f"{self.sync_stats['avg_sync_time']:.2f}s",
            "last_sync": self.sync_stats["last_sync_time"],
            "connection_status": "Connected" if self.sf else "Disconnected"
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Salesforce connection and return status"""
        try:
            if not self.sf:
                await self.initialize()
            
            # Simple query to test connection
            result = self.sf.query("SELECT Id FROM User LIMIT 1")
            
            if result["records"]:
                return {
                    "status": "success",
                    "message": "Salesforce connection active",
                    "last_test": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error", 
                    "message": "No data returned from Salesforce"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}"
            }
