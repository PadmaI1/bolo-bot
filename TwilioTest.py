import os
from twilio.rest import Client
from dotenv import load_dotenv
load_dotenv()
# Set environment variables for your credentials
# Read more at http://twil.io/secure

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)

call = client.calls.create(
  url="http://demo.twilio.com/docs/voice.xml",
  to="+916397983037",
  from_="+12294665688"
)

print(call.sid)