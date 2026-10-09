"""
📧 Email Service - Send call summaries via email
Supports Gmail SMTP for sending professional call summaries
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """
    📧 Email Service for sending call summaries
    Uses Gmail SMTP or any SMTP server
    """
    
    def __init__(self):
        """Initialize email service with credentials from .env"""
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.sender_name = os.getenv("SENDER_NAME", "Murf AI Sales Team")
        
        if not self.sender_email or not self.sender_password:
            logger.warning("⚠️ Email credentials not configured in .env")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"✅ Email service initialized - Sender: {self.sender_email}")
    
    async def send_sales_summary_email(
        self, 
        recipient_email: str, 
        recipient_name: str,
        call_summary: Dict[str, Any]
    ) -> bool:
        """
        📧 Send B2B Sales call summary email
        
        Args:
            recipient_email: Customer's email address
            recipient_name: Customer's name
            call_summary: Call summary data with interest, use case, etc.
            
        Returns:
            bool: True if email sent successfully
        """
        if not self.enabled:
            logger.warning("⚠️ Email service disabled - missing credentials")
            return False
        
        try:
            # Extract call data
            interest_level = call_summary.get("interest_level", "unknown")
            use_case = call_summary.get("use_case", "Not specified")
            lead_score = call_summary.get("lead_score", 0)
            next_steps = call_summary.get("next_steps", "Follow-up call")
            duration = call_summary.get("duration_seconds", 0)
            
            # Create email
            subject = f"Thank you for your time, {recipient_name}! - Murf AI Follow-up"
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .highlight {{ background: #fff; padding: 15px; border-left: 4px solid #667eea; margin: 20px 0; }}
        .cta-button {{ background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎙️ Murf AI - Voice Technology That Speaks Volumes</h1>
        </div>
        <div class="content">
            <p>Namaste <strong>{recipient_name}</strong>,</p>
            
            <p>Thank you for taking the time to speak with me today! Main bahut khush hun ki aapne <strong>{duration // 60} minutes</strong> diye humari conversation ke liye.</p>
            
            <div class="highlight">
                <h3>📊 Conversation Summary</h3>
                <p><strong>Your Interest:</strong> {interest_level.title()}</p>
                <p><strong>Use Case:</strong> {use_case}</p>
                <p><strong>Lead Score:</strong> {lead_score}/10</p>
            </div>
            
            <h3>🚀 Why Murf AI for {use_case}?</h3>
            <ul>
                <li><strong>80% Faster:</strong> Voice content production compared to traditional methods</li>
                <li><strong>Premium Voices:</strong> 160+ natural-sounding AI voices in 20+ languages</li>
                <li><strong>Hindi-English Bilingual:</strong> Perfect for Indian market with code-switching</li>
                <li><strong>API Integration:</strong> Seamless workflow automation</li>
                <li><strong>Studio Quality:</strong> Professional-grade audio output</li>
            </ul>
            
            <div class="highlight">
                <h3>📅 Next Steps: {next_steps}</h3>
                <p>Main aapko ek <strong>live demo</strong> dikhana chahta hun jahan aap dekh sakte hain ki Murf AI aapke {use_case} workflow ko kaise transform kar sakta hai.</p>
            </div>
            
            <a href="https://murf.ai/demo" class="cta-button">🎯 Schedule Your Free Demo</a>
            
            <p style="margin-top: 30px;">Koi bhi sawal ho toh feel free to reach out. Main hamesha available hun!</p>
            
            <p><strong>Best regards,</strong><br>
            Shaan<br>
            Senior B2B Sales Consultant<br>
            Murf AI<br>
            📞 +91-XXXX-XXXX-XX<br>
            📧 {self.sender_email}</p>
            
            <div class="footer">
                <p>Murf AI - Transforming Voice Content Production Since 2020</p>
                <p>🌐 <a href="https://murf.ai">murf.ai</a> | 📱 Follow us on LinkedIn</p>
            </div>
        </div>
    </div>
</body>
</html>
            """
            
            return await self._send_email(recipient_email, subject, html_body)
            
        except Exception as e:
            logger.error(f"❌ Failed to send sales summary email: {e}")
            return False
    
    async def send_real_estate_summary_email(
        self, 
        recipient_email: str, 
        recipient_name: str,
        call_summary: Dict[str, Any]
    ) -> bool:
        """
        🏠 Send Real Estate call summary email
        
        Args:
            recipient_email: Customer's email address
            recipient_name: Customer's name
            call_summary: Call summary data with budget, location, etc.
            
        Returns:
            bool: True if email sent successfully
        """
        if not self.enabled:
            logger.warning("⚠️ Email service disabled - missing credentials")
            return False
        
        try:
            # Extract call data
            budget_range = call_summary.get("budget_range", "Not specified")
            location_preference = call_summary.get("location_preference", "Hyderabad")
            property_type = call_summary.get("property_type", "2BHK/3BHK")
            qualification_score = call_summary.get("qualification_score", 0)
            next_steps = call_summary.get("next_steps", "Site visit")
            duration = call_summary.get("duration_seconds", 0)
            
            # Create email
            subject = f"Premium Properties in {location_preference} - BB Ventures"
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .property-card {{ background: white; padding: 20px; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .highlight {{ background: #fff; padding: 15px; border-left: 4px solid #11998e; margin: 20px 0; }}
        .cta-button {{ background: #11998e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
        .badge {{ display: inline-block; background: #38ef7d; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px; margin: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 BB Ventures - Your Dream Home Awaits</h1>
            <p>Premium Properties in Hyderabad</p>
        </div>
        <div class="content">
            <p>Namaste <strong>{recipient_name} ji</strong>,</p>
            
            <p>Aapki baat sunke main bahut khush hua! Aapne <strong>{duration // 60} minutes</strong> time diya hamari property discussion ke liye. Dhanyavaad!</p>
            
            <div class="highlight">
                <h3>🎯 Your Requirements</h3>
                <p><strong>Budget:</strong> {budget_range}</p>
                <p><strong>Location:</strong> {location_preference}</p>
                <p><strong>Property Type:</strong> {property_type}</p>
                <p><strong>Qualification Score:</strong> {qualification_score}/10</p>
            </div>
            
            <h3>🏘️ Handpicked Properties for You</h3>
            
            <div class="property-card">
                <h4>🌟 Premium 3BHK - Gachibowli</h4>
                <p><strong>₹85 Lakhs</strong> | 1,450 sq.ft | Ready to Move</p>
                <span class="badge">Gated Community</span>
                <span class="badge">Clubhouse</span>
                <span class="badge">24/7 Security</span>
                <p>Perfect for families! Near Wipro, Infosys, and top schools.</p>
            </div>
            
            <div class="property-card">
                <h4>🌟 Luxury 2BHK - Hitec City</h4>
                <p><strong>₹65 Lakhs</strong> | 1,200 sq.ft | Under Construction</p>
                <span class="badge">Modern Amenities</span>
                <span class="badge">Gym & Pool</span>
                <span class="badge">Prime Location</span>
                <p>Walking distance to Hitec City metro, Microsoft, Google offices.</p>
            </div>
            
            <div class="highlight">
                <h3>📅 Next Steps: {next_steps}</h3>
                <p>Main aapko personally <strong>site visit</strong> karwaana chahta hun. Aap actual property dekh sakte hain aur feel kar sakte hain ki ye aapke liye sahi hai ya nahi.</p>
                <p><strong>Available Slots:</strong></p>
                <ul>
                    <li>Tomorrow (Sunday) - 10 AM to 6 PM</li>
                    <li>Monday - 4 PM onwards</li>
                    <li>Tuesday - Flexible timing</li>
                </ul>
            </div>
            
            <a href="https://bbventures.com/schedule-visit" class="cta-button">📅 Schedule Site Visit</a>
            
            <h3>💎 Why Choose BB Ventures?</h3>
            <ul>
                <li><strong>15+ Years Experience:</strong> Hyderabad real estate experts</li>
                <li><strong>5,000+ Happy Families:</strong> Trusted by thousands</li>
                <li><strong>Zero Brokerage:</strong> Direct from builders</li>
                <li><strong>Home Loan Assistance:</strong> Up to 90% financing</li>
                <li><strong>Legal Verification:</strong> Complete document check</li>
            </ul>
            
            <p style="margin-top: 30px;">Aapke dream home ki journey main aapke saath hun! Koi bhi sawaal ho toh bilkul puchiye.</p>
            
            <p><strong>Regards,</strong><br>
            Rohan Reddy<br>
            Senior Property Consultant<br>
            BB Ventures<br>
            📞 +91-XXXX-XXXX-XX<br>
            📧 {self.sender_email}</p>
            
            <div class="footer">
                <p>BB Ventures - Building Dreams Since 2008</p>
                <p>🌐 <a href="https://bbventures.com">bbventures.com</a> | 📱 Follow us for latest properties</p>
            </div>
        </div>
    </div>
</body>
</html>
            """
            
            return await self._send_email(recipient_email, subject, html_body)
            
        except Exception as e:
            logger.error(f"❌ Failed to send real estate summary email: {e}")
            return False
    
    async def _send_email(self, recipient_email: str, subject: str, html_body: str) -> bool:
        """
        Internal method to send email via SMTP
        
        Args:
            recipient_email: Recipient's email
            subject: Email subject
            html_body: HTML email body
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Attach HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Secure connection
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMTP error: {e}")
            return False


# Global instance
email_service = EmailService()
