# import africastalking

# # Initialize Africa's Talking
# africastalking.initialize(
#     username='Codewithaltech',
#     api_key=''
    
# )

# # Get the SMS service
# sms = africastalking.SMS

# class SendSMS:  # Class names should use CamelCase by convention
#     def send(self, recipients, message, sender):
#         try:
#             # Send the message
#             response = sms.send(message, recipients, sender)
#             print(response)
#             return response
#         except Exception as e:
#             print(f'Houston, we have a problem: {e}')
#             return None

# # Usage
# if __name__ == "__main__":
#     # Create instance of SendSMS
#     sms_sender = SendSMS()
    
#     # Set the parameters
#     recipients = ["+256708215305"]
#     message = "Hey AT Ninja!"
#     sender = "ATUpdates"
    
#     # Call the send method
#     sms_sender.send(recipients, message, sender)

# @app.route('/sms/delivery', methods=['POST'])
# def sms_delivery_callback():
#     try:
#         # Africa's Talking sends delivery report data as form data
#         data = request.form.to_dict()
#         print(f"Received delivery report: {data}")

#         # Example payload:
#         # {
#         #     'status': 'Success',
#         #     'phoneNumber': '+256708215305',
#         #     'messageId': 'ATXid_123456789',
#         #     'statusCode': '101',
#         #     'cost': 'UGX 50'
#         # }

#         # Process the delivery report (e.g., log to database, update status)
#         status = data.get('status')
#         phone_number = data.get('phoneNumber')
#         message_id = data.get('messageId')
#         cost = data.get('cost')

#         # Add your logic here (e.g., update database with delivery status)
#         print(f"Delivery status for {phone_number}: {status}, Message ID: {message_id}, Cost: {cost}")

#         # Return HTTP 200 OK to acknowledge receipt
#         return jsonify({'status': 'success'}), 200
#     except Exception as e:
#         print(f"Error processing delivery callback: {str(e)}")
#         # Still return 200 to prevent retries, but log the error
#         return jsonify({'status': 'error', 'message': str(e)}), 200