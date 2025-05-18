import africastalking
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

from luco.sms_schemas import SMSMessageCreate


project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

# from sms_schemas import SMSMessageCreate


load_dotenv()
print("Environment loaded")

class LucoSMS:

    def __init__(self, api_key=None, username='sandbox', sender_id='1234'):
        self.api_key = api_key or os.getenv("SANDBOX_API_KEY")
        print(f"API Key available: {'Yes' if self.api_key else 'No'}")
        if not self.api_key:
            raise ValueError("API key must be provided either in constructor or as environment variable")
        
        print(f"Initializing AfricasTalking with username: {username}")
        africastalking.initialize(username=username, api_key=self.api_key)
        self.sms = africastalking.SMS

    def send_message(self, message: str, recipients: list[str] ,sender_id: str = None):
        print(f"Preparing to send message to {recipients}")
        # Validate input using Pydantic model
        sms_data = SMSMessageCreate(message=message, recipients=recipients)

        try:
            print("Sending SMS...")
            response = self.sms.send(sms_data.message, sms_data.recipients, sender_id=sender_id)
            return response
        except Exception as e:
            print(f"Error details: {str(e)}")
            raise Exception(f"Failed to send SMS: {str(e)}")

if __name__ == "__main__":
    try:
        print("Starting SMS test...")
        # Create an instance of LucoSMS
        sms = LucoSMS()
        
        # Test message and recipients
        message = "Hello! This is a test message from LucoSMS."
        recipients = ["+256708215305"]  # Replace with actual test phone number
        
        # Send the message
        print(f"Sending test message: {message}")
        response = sms.send_message(message, recipients)
        print("SMS sent successfully!")
        print("Response:", response)
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")


