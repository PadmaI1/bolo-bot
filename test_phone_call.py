"""
Test script for making outbound phone calls using Twilio
Run this after configuring Twilio credentials in .env
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_phone_call():
    """Test making an outbound phone call"""
    
    # Configuration
    BASE_URL = "http://localhost:8000"
    YOUR_PHONE_NUMBER = input("Enter your phone number (format: +1234567890): ")
    
    # Choose call type
    print("\nSelect call type:")
    print("1. B2B Sales Agent")
    print("2. Real Estate Agent")
    choice = input("Enter choice (1 or 2): ")
    
    call_type = "b2b_sales" if choice == "1" else "real_estate"
    
    # Lead information
    lead_info = {
        "name": input("\nEnter your name: "),
        "company": input("Enter company name (or 'N/A'): "),
        "context": "Testing AI phone call system"
    }
    
    # Make the call
    print(f"\n📞 Making outbound call to {YOUR_PHONE_NUMBER}...")
    print(f"Call type: {call_type}")
    print(f"Lead info: {lead_info}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}/api/phone/call/outbound",
                json={
                    "phone_number": YOUR_PHONE_NUMBER,
                    "call_type": call_type,
                    "lead_info": lead_info
                }
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    print("\n✅ Call initiated successfully!")
                    print(f"Call SID: {result.get('call_sid')}")
                    print(f"Status: {result.get('status')}")
                    print(f"\n🎉 Your phone should ring in a few seconds!")
                    print(f"The AI agent will start the conversation automatically.")
                    
                    # Monitor call status
                    call_sid = result.get('call_sid')
                    if call_sid:
                        print(f"\n📊 Monitoring call status...")
                        for i in range(10):
                            await asyncio.sleep(3)
                            async with session.get(f"{BASE_URL}/api/phone/call/{call_sid}") as status_response:
                                if status_response.status == 200:
                                    status_data = await status_response.json()
                                    print(f"Status: {status_data.get('status')} | Duration: {status_data.get('duration', 0)}s")
                                    if status_data.get('status') == 'completed':
                                        print("\n✅ Call completed!")
                                        break
                else:
                    print(f"\n❌ Call failed: {result}")
                    
        except Exception as e:
            print(f"\n❌ Error: {e}")

async def test_sms():
    """Test sending an SMS"""
    
    BASE_URL = "http://localhost:8000"
    phone_number = input("Enter phone number to send SMS (format: +1234567890): ")
    message = input("Enter message: ")
    
    print(f"\n📱 Sending SMS to {phone_number}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}/api/phone/sms",
                json={
                    "phone_number": phone_number,
                    "message": message
                }
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    print("\n✅ SMS sent successfully!")
                    print(f"SID: {result.get('sid')}")
                else:
                    print(f"\n❌ SMS failed: {result}")
                    
        except Exception as e:
            print(f"\n❌ Error: {e}")

async def check_active_calls():
    """Check active phone calls"""
    
    BASE_URL = "http://localhost:8000"
    
    print("\n📞 Checking active calls...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/api/phone/active-calls") as response:
                result = await response.json()
                
                if response.status == 200:
                    print(f"\n✅ Active calls: {result.get('total', 0)}")
                    for call_sid, call_info in result.get('active_calls', {}).items():
                        print(f"\nCall SID: {call_sid}")
                        print(f"  To: {call_info.get('to_number')}")
                        print(f"  Type: {call_info.get('call_type')}")
                        print(f"  Status: {call_info.get('status')}")
                else:
                    print(f"\n❌ Failed: {result}")
                    
        except Exception as e:
            print(f"\n❌ Error: {e}")

async def main():
    """Main menu"""
    
    print("=" * 60)
    print("🤖 AI Phone Agent Test Suite")
    print("=" * 60)
    
    # Check Twilio configuration
    if not os.getenv("TWILIO_ACCOUNT_SID") or not os.getenv("TWILIO_AUTH_TOKEN"):
        print("\n⚠️ Twilio not configured!")
        print("Please add the following to your .env file:")
        print("  TWILIO_ACCOUNT_SID=your_account_sid")
        print("  TWILIO_AUTH_TOKEN=your_auth_token")
        print("  TWILIO_PHONE_NUMBER=+1234567890")
        print("  WEBHOOK_BASE_URL=https://your-server.com")
        print("\n💡 For local testing, use ngrok:")
        print("  1. Run: ngrok http 8000")
        print("  2. Copy the https URL to WEBHOOK_BASE_URL in .env")
        return
    
    while True:
        print("\n\nSelect an option:")
        print("1. Make test phone call")
        print("2. Send test SMS")
        print("3. Check active calls")
        print("4. Exit")
        
        choice = input("\nEnter choice: ")
        
        if choice == "1":
            await test_phone_call()
        elif choice == "2":
            await test_sms()
        elif choice == "3":
            await check_active_calls()
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
