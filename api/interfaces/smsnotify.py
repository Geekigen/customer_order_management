import africastalking
from customer_app import settings


class SendSms:
    def __init__(self):
        """
        Initialize AfricasTalking API credentials when the class is instantiated
        """
        africastalking.initialize(
            username=settings.AFRICAS_USERNAME,
            api_key=settings.AFRICASTALKING_API_KEY
        )
        self.sms = africastalking.SMS
        self.sender = settings.AFRICASTALKING_SENDER_ID

    def send(self, phone_number, message):
        """
        Send message to a phone number
        """
        try:
            # Make sure the phone number is properly formatted
            if not phone_number.startswith('+'):
                phone_number = '+' + phone_number

            # Send the message
            response = self.sms.send(message, [phone_number], self.sender)
            return response
        except Exception as e:
            return {'error': str(e)}


# Usage example
# if __name__ == "__main__":
#     test = SendSms()
#     response = test.send('+254719485369', 'Test message')
#     print(response)