import os
import sys
from abc import ABC, abstractmethod

from twilio.rest import Client

from src.config.logging_config import Logger
from src.utils.message_utils import convert_to_whatsapp_number_format

logger = Logger('myfoodrepo.messaging_service').get_logger()


class MessagingService(ABC):

    @abstractmethod
    def send_message(self, to, body):
        pass

    @abstractmethod
    def initialize_service(self):
        pass


"""
Obsolete class, unused to to Whatsapp-related issues.
"""
class WhatsAppService(MessagingService):
    def __init__(self):
        self.phone_number = 'whatsapp:' + str(os.environ.get('TWILIO_PHONE_NUMBER'))
        self.client = Client(os.environ.get('TWILIO_ACCOUNT_SID'),
                             os.environ.get('TWILIO_AUTH_TOKEN'))

    def initialize_service(self):
        pass

    def send_message(self, to, body):
        whatsapp_number = convert_to_whatsapp_number_format(to)
        message = self.client.messages.create(body=body,
                                              from_=self.phone_number,
                                              to=whatsapp_number)
        logger.debug(f"WhatsApp Message ID: {message.sid}, with status: {message.status}")


class SMSService(MessagingService):
    """
    Twilio SMS service class, handling main functions to be able to send SMSes to users.
    """

    def __init__(self):
        self.sender_id = os.environ.get('TWILIO_SMS_SENDER_ID')

        self.client = Client(os.environ.get('TWILIO_ACCOUNT_SID'),
                             os.environ.get('TWILIO_AUTH_TOKEN'))

    def initialize_service(self):
        pass

    def send_message(self, to, body):
        message = self.client.messages.create(body=body,
                                              from_=self.sender_id,
                                              to=to,
                                              risk_check="disable")
        logger.debug(f"SMS Message ID: {message.sid}, with status: {message.status}")
        return message