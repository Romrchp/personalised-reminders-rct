from datetime import datetime,time
import os

from twilio.twiml.messaging_response import MessagingResponse

from src.data_manager.message import get_user_messages
from src.data_manager.nutritional_profiling import retrieve_nutritional_information, calculate_eating_consistency
from src.communication.messaging_service import SMSService, WhatsAppService
from src.communication.twilio_tool import NewTwilioConversationManager
from src.config.logging_config import Logger
from src.utils.localization_utils import prompt_language_formatting
from src.prompts.prompts_templates import CONVERSATION_PERSONA, CONVERSATION_PROMPT, CONVERSATION_ROLE, NEARLY_REACHED_MESSAGE_LIMIT_PROMPT, REACHED_MESSAGE_LIMIT_PROMPT, USER_PROFILE,\
                                          CONVERSATION_FEW_SHOTS, CONVERSATION_COT, CONVERSATION_RULES
from src.constants import (ASSISTANT_ROLE, GPT_4_O, SYSTEM_ROLE,
                           USER_ROLE, USERS_MESSAGES_LIMIT)
from src.data_manager.meal import get_recent_meals_string_for_user
from src.data_manager.user import get_user
from src.openai_client import OpenAIChatClient


logger = Logger('myfoodrepo.response_manager').get_logger()
chat_client = OpenAIChatClient(os.environ.get('OPENAI_API_KEY'))

def exceeds_message_limit(user_id) :
    """
    Checking if the user has reached the fixed messages limit for the present day.

    Args:
        user: The `User` for which we should check the limit

    Returns:
        Tuple[bool, int]: (Whether limit is exceeded, number of messages today)
    """

    todays_messages  = get_user_messages(user_id)
    midnight_today = datetime.combine(datetime.today(), time.min)
    todays_messages  = [
    message for message in todays_messages 
    if message.datetime >= midnight_today and message.role == "user"
                        ]
    print(todays_messages,len(todays_messages)+1)
    
    return (len(todays_messages) + 1 > USERS_MESSAGES_LIMIT, len(todays_messages) + 1)


def generate_response(from_number, body, system_prompt,twilio_message_id) -> str:
    resp = ""
    if body:
        chat_client.add_message_from_phone_number(from_number, SYSTEM_ROLE, system_prompt,None,None)

        chat_client.add_message_from_phone_number(from_number, USER_ROLE, body,twilio_message_id,None)

        openai_response = chat_client.create_chat_completion(GPT_4_O, from_number, 1)

        logger.debug("OpenAI Correctly Formulated a Response")
        resp = openai_response
    else:
        resp = "Sorry, I couldn't generate a response"

    return resp


def process_openai_response(app, from_number, body, response_data, timer, twilio_message_id, msg_type="SMS"):
    with app.app_context(): 

        user = get_user(from_number)

        messages_limit_exceeded, msg_nb_today = exceeds_message_limit(user.id)
        if messages_limit_exceeded :
            logger.info(f"User {user.id} has exceeded the number of messages for today. Not sending a response.")
        
        else :
            recent_meals = get_recent_meals_string_for_user(user.myfoodrepo_key)
            nutritional_information = retrieve_nutritional_information(user)
            consistency_metrics = calculate_eating_consistency(user)
            user_language = prompt_language_formatting(user.language)
            current_datetime = datetime.now()

            base_prompt = CONVERSATION_ROLE.format(current_datetime = current_datetime)

            base_prompt += USER_PROFILE.format(
                age = user.age,
                gender = user.gender,
                diet_goal = user.diet_goal,
                diet_information = nutritional_information,
                recent_meals = recent_meals,
                current_logging_streak = consistency_metrics['current_streak'],
                prefered_language = user_language)
            
            meal_info_prompt = base_prompt + CONVERSATION_PERSONA + CONVERSATION_FEW_SHOTS + CONVERSATION_COT + CONVERSATION_RULES


            if msg_nb_today == USERS_MESSAGES_LIMIT - 1 :
                meal_info_prompt += NEARLY_REACHED_MESSAGE_LIMIT_PROMPT

            elif msg_nb_today == USERS_MESSAGES_LIMIT :
                meal_info_prompt += REACHED_MESSAGE_LIMIT_PROMPT

            response_text = generate_response(from_number, body, meal_info_prompt,twilio_message_id)
            response_data['response'] = response_text

            if timer.is_alive():
                timer.cancel()

            manager: NewTwilioConversationManager
            if msg_type == 'WhatsApp':
                manager = NewTwilioConversationManager(WhatsAppService())
            else:
                manager = NewTwilioConversationManager(SMSService())
            open_ai_response = manager.send_message(from_number, response_text)
            chat_client.add_message(user.id,ASSISTANT_ROLE,open_ai_response.body,open_ai_response.sid,None)


def generate_error_response() -> MessagingResponse:
    resp = MessagingResponse()

    resp.message("An error occurred while processing your message.")
    logger.error(str(resp))
    return resp


def send_interim_response(to_number, response_data):
    pass
