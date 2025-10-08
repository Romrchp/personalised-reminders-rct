from src.config.logging_config import Logger

from ..constants import ASSISTANT_ROLE
from ..data_manager.message import db_add_message_from_phone_number
from ..data_manager.user import get_all_users,update_user_study_end
from .messaging_service import SMSService
from .twilio_tool import NewTwilioConversationManager

logger = Logger('myfoodrepo.conversation_starter').get_logger()


def end_conversations(service=SMSService()):
    """
    Ending all conversations with active users in the study that have not withdrawn
    """

    all_users = get_all_users()
    manager = NewTwilioConversationManager(service)

    logger.info("RCT's ending - sending a final message to all users who have not withdrawn in the present cohort.")
    for user in all_users:
        if not user.withdrawal and user.study_ended : 
            goodbye_message = manager.send_goodbye_message(user.phone_number)

            status_log, status = db_add_message_from_phone_number(
                user.phone_number,
                ASSISTANT_ROLE,
                goodbye_message.body,
                goodbye_message.sid,
                None
            )


            if status != 200:
                logger.error(status_log)
    logger.info("All ending messages have been sent to non-withdrawn users!")

def end_specific_conversation(user,service=SMSService()): 
    """
    Ending the conversation with a specific user and updating their participation status

    Args:
        user: The User instance we aim to end the participation of
    """
    manager = NewTwilioConversationManager(service)
    logger.info(f"Ending the conversation for user {user.id}")

    goodbye_message = manager.send_goodbye_message(user.phone_number)
    status_log, status = db_add_message_from_phone_number(user.phone_number,
                                                          ASSISTANT_ROLE,
                                                          goodbye_message.body,
                                                          goodbye_message.sid,
                                                          None)
    update_user_study_end(user.phone_number,True)
    if status != 200:
        logger.error(status_log)

