import json
import os
import random

from twilio.rest import Client

from src.data_manager.meal import get_recent_meals_string_for_user
from src.communication.messaging_service import MessagingService
from src.config.logging_config import Logger
from src.constants import (ANDROID_APP_LINK, FEEDBACK_SURVEY, IOS_APP_LINK, SMS_SENDER_ID,
                           WHATSAPP_SENDER_ID)
from src.data_manager.user import get_user
from src.utils.localization_utils import (get_localized_random_string,
                                          get_localized_string)
from src.utils.message_utils import convert_to_whatsapp_number_format

logger = Logger('myfoodrepo.twilio_tool').get_logger()


class NewTwilioConversationManager:
    def __init__(self, messaging_service: MessagingService):
        """
        Initializes the TwilioConversationManager with a messaging service.

        :param messaging_service: An instance of a class that implements the MessagingService interface.
        """
        self.messaging_service = messaging_service
        self.messaging_service.initialize_service()

    def send_message(self, to, body):
        """
        Sends a message using the configured messaging service.

        :param to: The recipient of the message.
        :param body: The content of the message.
        """
        
        message = self.messaging_service.send_message(to, body)
        return message

    def send_welcome_message(self, to_number): 
        """
        Sends a welcome message using the configured messaging service.

        :param to_number: The recipient of the message.
        """
        user = get_user(to_number)
        language = user.language if user else 'en'

        logger.info(f"User's study group is {user.study_group}")

        if user.study_group in (2, 3):
            welcome_message = get_localized_string('welcome_message_allowed_to_chat', language)
        else:
            welcome_message = get_localized_string('welcome_message', language)
            #logger.info(f"I am indeed going there {user.study_group}")
        
        download_app_message = get_localized_string('download_app_message', language)
        your_key_message = get_localized_string('welcome_key_message', language)
        final_note = get_localized_string('welcome_final_note', language)

        welcome_message += f"\n\n{download_app_message}\niOS: {IOS_APP_LINK}\nAndroid: {ANDROID_APP_LINK}"
        welcome_message += f"\n\n{your_key_message} {user.myfoodrepo_key}"
        welcome_message += f"\n\n{final_note}"

        welcome_message_sent = self.messaging_service.send_message(to_number, welcome_message)

        return welcome_message_sent

    def send_goodbye_message(self, to_number): 
        """
        Sends a goodbye message signalling the end of the study to the user.

        :param to_number: The recipient of the message.
        """
        user = get_user(to_number)
        language = user.language if user else 'en'
        goodbye_message = ""

        has_started = (user.last_meal_log != None)

        if (user.study_group == 2) or (user.study_group  == 3) :
            if has_started:
                    goodbye_message = get_localized_string('goodbye_allowed_to_chat_message_started', language)
                    goodbye_message += f"\n\n{get_localized_string('goodbye_message_email_info', language)}"

            else:
                goodbye_message = get_localized_string('goodbye_message', language)
                goodbye_message += f"\n\n{get_localized_string('never_started', language)}"
        
        else:
            goodbye_message = get_localized_string('goodbye_message', language)
            if has_started :
                goodbye_message += f"\n\n{get_localized_string('goodbye_message_email_info', language)}"
            else:
                goodbye_message += f"\n\n{get_localized_string('never_started', language)}"


        goodbye_message += f"\n\n{get_localized_string('goodbye_final_note_message', language)}"
        goodbye_message_sent = self.messaging_service.send_message(to_number, goodbye_message)

        return goodbye_message_sent
