import africastalking
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from luco.sms_schemas import SMSMessageCreate

# Set project root for imports
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

load_dotenv()
# print("Environment loaded")

class LucoSMS:
    def __init__(self, api_key=None, username=None, sender_id=None):
        # Use live username from env or provided parameter
        self.username = username or os.getenv("AT_LIVE_USERNAME")
        if not self.username:
            raise ValueError("Live username must be provided either in constructor or as AT_LIVE_USERNAME environment variable")

        # Use live API key from env or provided parameter
        self.api_key = api_key or os.getenv("AT_LIVE_API_KEY")
        # print(f"API Key available: {'Yes' if self.api_key else 'No'}")
        if not self.api_key:
            raise ValueError("API key must be provided either in constructor or as AT_LIVE_API_KEY environment variable")

        # Use registered Sender ID from env or provided parameter
        self.sender_id = sender_id or os.getenv("AT_SENDER_ID")
        if not self.sender_id:
            raise ValueError("Sender ID must be provided either in constructor or as AT_SENDER_ID environment variable")
        
        # print(f"Initializing AfricasTalking with username: {self.username}, sender_id: {self.sender_id}")
        africastalking.initialize(username=self.username, api_key=self.api_key)
        self.sms = africastalking.SMS

    def send_message(self, message: str, recipients: list[str], sender_id: str = None):
        # print(f"Preparing to send message to {recipients}")
        # Use provided sender_id or fallback to initialized sender_id
        effective_sender_id = sender_id or self.sender_id
        if not effective_sender_id:
            raise ValueError("Sender ID must be specified for live environment")


        sms_data = SMSMessageCreate(message=message, recipients=recipients)

        try:
            # print(f"Sending SMS with sender_id: {effective_sender_id}")
            response = self.sms.send(sms_data.message, sms_data.recipients, sender_id=effective_sender_id)
            # print(f"SMS sent successfully: {response}")
            return response
        except Exception as e:
            # print(f"Error details: {str(e)}")
            raise Exception(f"Failed to send SMS: {str(e)}")

# if __name__ == "__main__":
    # try:
    #     print("Starting SMS test in live environment...")
    #     # Create an instance of LucoSMSLive
    #     sms = LucoSMS()
        
    #     # Test message and recipients
    #     message = "Hello! This is a test message from LucoSMS in live environment."
    #     recipients = ["+256708215305"]  # Replace with actual test phone number
        
    #     # Send the message
    #     print(f"Sending test message: {message}")
    #     response = sms.send_message(message, recipients)
    #     print("SMS sent successfully!")
    #     print("Response:", response)
        
    # except Exception as e:
    #     print(f"Error occurred: {str(e)}")