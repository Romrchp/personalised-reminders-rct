from src.config.logging_config import Logger

from ..constants import ASSISTANT_ROLE
from ..data_manager.message import db_add_message_from_phone_number
from ..data_manager.user import get_all_users
from .messaging_service import SMSService
from .twilio_tool import NewTwilioConversationManager

logger = Logger('myfoodrepo.conversation_starter').get_logger()


def start_conversations(service=SMSService()): 
    """
    Starting all conversations for users in the cohort
    """
    all_users = get_all_users()
    manager = NewTwilioConversationManager(service)

    logger.info("Starting a new conversation for all users in the system.")
    for user in all_users:
        welcome_message = manager.send_welcome_message(user.phone_number)

        status_log, status = db_add_message_from_phone_number(user.phone_number,
                                                              ASSISTANT_ROLE,
                                                              welcome_message.body,
                                                              welcome_message.sid,
                                                              None)
        if status != 200:
            logger.error(status_log)


def start_specific_conversation(user,service=SMSService()): 
    """
    Start the conversation for a specific user of the cohort.

    Args:
        -  user: The User object subject to conversation start

    """
    manager = NewTwilioConversationManager(service)
    logger.info(f"Starting a new conversation for user {user.id}")

    welcome_message = manager.send_welcome_message(user.phone_number)
    status_log, status = db_add_message_from_phone_number(user.phone_number,
                                                          ASSISTANT_ROLE,
                                                          welcome_message.body,
                                                          welcome_message.sid,
                                                          None)
    if status != 200:
        logger.error(status_log)
