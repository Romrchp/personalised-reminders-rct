from collections import defaultdict
import datetime
import os
import random
import pytz

from src.communication.messaging_service import SMSService
from src.communication.twilio_tool import NewTwilioConversationManager
from src.config.logging_config import Logger
from src.constants import ASSISTANT_ROLE, GPT_4_O, SYSTEM_ROLE, GPT_4_1_MINI
from src.data_manager.meal import get_recent_meals_string_for_user
from src.data_manager.message import get_user_messages
from src.data_manager.models import User
from src.data_manager.nutritional_profiling import retrieve_nutritional_information, calculate_eating_consistency
from src.data_manager.reminder import get_previous_reminder_texts
from src.openai_client import OpenAIChatClient
from src.prompts.prompts_templates import *
from src.utils.localization_utils import (
    get_localized_meal_type,
    get_localized_random_string,
    prompt_language_formatting
)

logger = Logger('myfoodrepo.reminder_manager').get_logger()
timezone = pytz.timezone('Europe/Zurich')
twilio_manager = NewTwilioConversationManager(SMSService())
chat_client = OpenAIChatClient(os.environ.get('OPENAI_API_KEY'))

def get_reminder_generators():
    """Returns a dictionary mapping study group to reminder generation function."""
    return {
        3: generate_personalised_reminder,
        1: generate_generic_reminder
    }

def get_time_since_last_log(user):
    """Calculate time since user's last meal log"""
    if user.last_meal_log is None:
        return datetime.timedelta.max
    
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    return now_utc - user.last_meal_log.astimezone(datetime.timezone.utc)


def get_time_since_last_reminder(user):
    """Calculate time since last reminder was sent to user"""
    last_messages = get_user_messages(user.id)
    last_reminder_time = max(
        (msg.datetime for msg in last_messages if msg.reminder_id is not None),
        default=None
    )
    
    if not last_reminder_time:
        return datetime.timedelta.max
        
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    return now_utc - last_reminder_time.astimezone(datetime.timezone.utc)

def get_time_since_welcome_message(user):
    """Calculate time since the user's earliest (welcome) message"""
    all_messages = get_user_messages(user.id)
    
    first_message_time = min(
        (msg.datetime for msg in all_messages),
        default=None
    )
    
    if not first_message_time:
        return datetime.timedelta.max 
    
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    return now_utc - first_message_time.astimezone(datetime.timezone.utc)


def format_timedelta(td):
    """
    Transforms a `timedelta` object to appropriate string format for the chatbot.

    Args:
        td: A `timedelta` object.

    Returns:
        str: A formatted string with time information.
    """
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes = remainder // 60
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    return ", ".join(parts) or "less than a minute"


def should_send_reminder(user: User) -> bool:
    """
    Determines whether a reminder should be sent based on user's activity.
    Reminder is automatically skipped if the user has more than 2 days inactivity.

    Args:
        user (User): The user to check.

    Returns:
        bool: True if the reminder should be sent, False otherwise.
    """
    try:

        time_since_welcome_message = get_time_since_welcome_message(user)

        if user.last_meal_log is None and user.withdrawal == False and time_since_welcome_message < datetime.timedelta(days=4):
            logger.info(f"User {user.id} has never logged a meal. Proceeding with reminder.")
            return True
        
        elif user.last_meal_log is None and user.withdrawal == False and time_since_welcome_message >= datetime.timedelta(days=4):
            logger.info(f"User {user.id} never participated. Skipping reminder.")
            return False
        
        time_since_last_log = get_time_since_last_log(user)

        if time_since_last_log > datetime.timedelta(days=2) or user.withdrawal == True:
            logger.info(f"User {user.id} hasn't logged meals in {time_since_last_log.days} days. Skipping reminder.")
            return False

        return True

    except Exception as e:
        logger.error(f"Failed to determine reminder eligibility for user {user.id}: {e}")
        return True  # still send reminder if in doubt


def should_skip_reminder(user_id):
    """
    Performs a coinflip to know whether a user's reminder should be skipped.
    Always send at least one reminder every two days (after 5 skips).
    Uses database to track skipped reminders for persistence across restarts.

    Args:
        user_id: The user's ID for which we want to know whether we should skip reminders or not.
    
    Returns:
        bool: True if reminder should be skipped, False otherwise.
    """
    try:
        
        recent_messages = get_user_messages(user_id) 
        reminder_messages = [msg for msg in recent_messages if msg.reminder_id is not None]
        
        # simply count consecutive skipped reminders by looking at time gaps
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        consecutive_skips = 0
        

        zurich_tz = pytz.timezone('Europe/Zurich')
        reminder_hours = [7, 12, 19]  # 7AM, 12PM, 7PM
        
        # Compute the number of consecutive occasions on which reminders have been skipped
        if reminder_messages:
            last_reminder_time = max(msg.datetime for msg in reminder_messages)
            last_reminder_utc = last_reminder_time.astimezone(datetime.timezone.utc)
            
            # Count missed reminder opportunities since last sent reminder
            current_time = now_utc.astimezone(zurich_tz)
            last_reminder_zurich = last_reminder_utc.astimezone(zurich_tz)
            
            # Calculate days between last reminder and now
            days_diff = (current_time.date() - last_reminder_zurich.date()).days
            
            if days_diff == 0:
                # If it's the sameday, count missed opportunities today
                current_hour = current_time.hour
                last_reminder_hour = last_reminder_zurich.hour
                
                missed_today = len([h for h in reminder_hours if last_reminder_hour < h <= current_hour])
                consecutive_skips = missed_today
            else:
                # If it's a different day, count all missed opportunities
                # Remaining opportunities on the day of last reminder
                last_day_remaining = len([h for h in reminder_hours if h > last_reminder_zurich.hour])
                
                full_days_missed = max(0, days_diff - 1) * 3
                
                current_hour = current_time.hour
                today_passed = len([h for h in reminder_hours if h <= current_hour])
                
                consecutive_skips = last_day_remaining + full_days_missed + today_passed
        else:
            # No reminders ever sent -> we send
            logger.info(f"User {user_id} has no previous reminders. Not skipping.")
            return False
        
        # Force send if we've skipped 5 or more consecutive opportunities (approx 2 days)
        if consecutive_skips >= 5:
            logger.info(f"User {user_id} has {consecutive_skips} consecutive skips. Forcing reminder.")
            return False
        
        # Perform coinflip for skip decision
        skip = random.randint(0, 1) == 0
        
        if skip:
            logger.info(f"User {user_id} reminder skipped by coinflip. Consecutive skips: {consecutive_skips + 1}")
        else:
            logger.info(f"User {user_id} reminder will be sent. Resetting skip count.")
            
        return skip
        
    except Exception as e:
        logger.error(f"Error in should_skip_reminder for user {user_id}: {e}")
        return False


def determine_warning(user):
    """
    Decides if the reminder should include a gentle warning to encourage app usage.
    
    If the time the user last logged a meal is between 1 and 2 days, we decide if we 
    should send a warning depending on when we sent the last reminder.
    
    In all other cases we do not include warnings. If the user is active, no warning, and if the
    user is fully inactive, reminder will simply be skipped.

    Args:
        user: User object for which the reminder is going to be sent.
    
    Returns:
        tuple: (
            timedelta: Time since last log
            bool: True if warning should be included,
            timedelta: Time since last reminder,
            bool: True if user never logged a meal
        )
    """
    try:

        time_since_last_log = get_time_since_last_log(user)
        time_since_last_reminder = get_time_since_last_reminder(user)

        # Check if user has never logged
        if user.last_meal_log is None:
            logger.info(f"User {user.id} has not logged meals yet. Gentle incent needed.")
            return datetime.timedelta.max, True, time_since_last_reminder, True
        
        # Different scenarios to include warnings based on activity patterns
        if datetime.timedelta(days=1) < time_since_last_log < datetime.timedelta(days=2):
            logger.info(f"User {user.id} has partial inactivity. Gentle incent included.")
            return time_since_last_log,True, time_since_last_reminder, False
           
        logger.info(f"No warning needed for user {user.id}.")
        return time_since_last_log,False, time_since_last_reminder, False
         
    except Exception as e:
        logger.error(f"Error in determining warning status for user {user.id}: {e}")
        return time_since_last_log, False, datetime.timedelta.max, False


import random

def select_personalization_prompt(user, last_used_prompt=None):
    """
    Selects an appropriate personalization prompt based on user's nutritional data.

    Args:
        user: User object with nutritional data
        last_used_prompt (str, optional): Identifier of the last used prompt to reduce repetition

    Returns:
        str: The selected personalization prompt
    """
    
    diet_info = retrieve_nutritional_information(user)
    diet_info = [str(info).lower() for info in diet_info if isinstance(info, str)]

    has_deficiency = any("low" in info for info in diet_info)
    has_excess = any("high" in info for info in diet_info)
    
    # Prompt pool with tags
    prompt_pool = [
        {"prompt": None, "tag": "skip", "weight": 0.8}, 
        {"prompt": NUTRITIONAL_DEFICIENCY_PROMPT, "tag": "deficiency", "weight": 2 if has_deficiency else 0.2},
        {"prompt": NUTRITIONAL_EXCESS_PROMPT, "tag": "excess", "weight": 2 if has_excess else 0.2},
        {"prompt": FUN_FACT_ENCOURAGEMENT_PROMPT, "tag": "fun_fact", "weight": 0.2 if (has_excess or has_deficiency) else 1.2},
    ]

    # Optional: reduce repetition of the last-used prompt
    #if last_used_prompt:
    #    for entry in prompt_pool:
    #        if entry["prompt"] == last_used_prompt:
    #            entry["weight"] *= 0.3  
    # Normalize and draw
    prompts, weights = zip(*[(entry["prompt"], entry["weight"]) for entry in prompt_pool])
    selected_prompt = random.choices(prompts, weights=weights, k=1)[0]

    return selected_prompt

def add_cot(prompt):
    if prompt == FUN_FACT_ENCOURAGEMENT_PROMPT :
        return FUN_FACT_ENCOURAGEMENT_COT
    elif prompt == NUTRITIONAL_DEFICIENCY_PROMPT:
        return NUTRITIONAL_DEFICIENCY_COT
    elif prompt == NUTRITIONAL_EXCESS_PROMPT :
        return NUTRITIONAL_EXCESS_COT
    else :
        return ""
    
class SafeDict(dict):
    def __missing__(self, key):
        return f'{{{key}}}'

def generate_personalised_reminder(user, meal_type, warning, tlr, tll, never_logged, app, reminder_id=None):
    """
    Generates the content of a personalised reminder based on user data.

    Args:
        user (User): User to send reminder to
        meal_type (str): The type of meal (Breakfast, Lunch, Dinner)
        warning (bool): Flag to indicate if the reminder should include a warning
        tlr (timedelta): Time since last reminder
        tll (timedelta): Time since last meal log
        never_logged (bool): Whether the user has never logged a meal
        app: The current Flask application
        reminder_id (int, optional): Unique identifier for the reminder
    
    Returns:
        str: The personalized reminder text
    """
    recent_meals = get_recent_meals_string_for_user(user.myfoodrepo_key,meals_nb=10)
    diet_information = retrieve_nutritional_information(user)
    consistency_metrics = calculate_eating_consistency(user)
    translated_meal_type = get_localized_meal_type(meal_type, user.language, app)
    formatted_user_language = prompt_language_formatting(user.language)
    previous_reminders = get_previous_reminder_texts(user) 

    # Strucruting the final prompt used to generate the reminder
    final_prompt= ""

    if tll > datetime.timedelta(minutes=30) :
        final_prompt = REMINDER_SYSTEM_ROLE_VANILLA.format(meal_type = translated_meal_type)

    else :
        final_prompt = REMINDER_SYSTEM_ROLE_RECENT_LOG

    final_prompt += SYSTEM_PERSONA

    final_prompt += USER_PROFILE.format(
                                age= user.age, gender = user.gender,
                                diet_goal = user.diet_goal, 
                                recent_meals = recent_meals,
                                diet_information = diet_information,
                                current_logging_streak = consistency_metrics['current_streak'],
                                prefered_language = formatted_user_language
    )
    final_prompt += REMINDER_CONTEXT.format(
                                        tlr = format_timedelta(tlr) if tlr is not datetime.timedelta.max else "No reminder ever sent.",
                                        previous_reminders = previous_reminders
                                    )
    
    if never_logged:
        final_prompt += NEVER_LOGGED_PROMPT
    elif warning:
        final_prompt += WARNING_PROMPT

    else: 
        additional_prompt = select_personalization_prompt(user)
        potential = ""
        if additional_prompt: 
            safe_data = SafeDict({
                'diet_information': diet_information,
                'diet_goal': user.diet_goal,
                'recent_meals': recent_meals
            })

            additional_guideline = additional_prompt.format_map(safe_data)

            cot_template = add_cot(additional_prompt)
            potential = cot_template.format_map(safe_data) if cot_template else ""

            final_prompt += additional_guideline


        final_prompt += COT_REASONING.format(prefered_language=formatted_user_language)
        final_prompt += potential

        final_prompt += FEW_SHOTS_PROMPTING.format(meal_type = translated_meal_type)


    final_prompt += INFLEXIBLE_RULES.format(prefered_language = formatted_user_language)

    logger.info("Preparing a PERSONALIZED reminder...")
    chat_client.add_message_from_phone_number(user.phone_number, SYSTEM_ROLE, final_prompt, None, None)
    openai_response = chat_client.create_chat_completion(GPT_4_O, user.phone_number, 1)
    logger.debug(f"OpenAI response is: {openai_response}")

    return openai_response


def generate_generic_reminder(user, meal_type, warning, tlr, tll, never_logged, app, reminder_id):
    """
    Selects a pre-defined static reminder to send to the user.

    Args:
        user (User): User to send reminder to
        meal_type (str): The type of meal (Breakfast, Lunch, Dinner)
        warning (bool): Flag to indicate if the reminder should include a warning
        never_logged (bool): Whether the user has never logged a meal
        tlr (timedelta): Time since last reminder
        app: The current Flask application
        reminder_id (int): Unique identifier for the reminder
    
    Returns:
        str: The selected static reminder text
    """
    logger.info("Preparing a GENERIC reminder...")
    translated_meal_type = get_localized_meal_type(meal_type, user.language, app)

    if warning and not never_logged:
        return get_localized_random_string('warning_reminder_static_messages', user.language, app).format(translated_meal_type)
    else:
        return get_localized_random_string('reminder_static_messages', user.language, app).format(translated_meal_type)


def send_reminder(user: User, meal_type: str, app, reminder_id):
    """
    Main function to send a reminder to a user for a specific meal type.

    Args:
        user (User): User to send reminder to
        meal_type (str): The type of meal (Breakfast, Lunch, Dinner)
        app: The current Flask application
        reminder_id (int): Unique identifier for the reminder
    """
    with app.app_context():
        try:
            # Determine if warning should be included
            tll, warning, tlr, never_logged = determine_warning(user)

            # Check if we should skip the reminder
            if should_skip_reminder(user.id) and not warning:
                logger.info(f"Reminder for user {user.id} has been skipped by coinflip.")
                return
                
            if not should_send_reminder(user):
                logger.info(f"Reminder for user {user.id} skipped due to >2 days inactivity.")
                return
    
            
            if warning is None:
                logger.warning(f"No valid warning condition found for user {user.id}. Fix it!")
                return

            # Get appropriate reminder generator for this user's study group
            reminder_generators = get_reminder_generators()
            if user.study_group not in reminder_generators:
                logger.warning(f"User {user.id} is not in a valid study group for reminders. Fix it!")
                return
    
            reminder_function = reminder_generators[user.study_group]
            response = reminder_function(user, meal_type, warning, tlr, tll, never_logged, app, reminder_id)
    
            if response not in ["RateLimitError","OpenAIError","UnexpectedError"] :
                try:
                    message_sent = twilio_manager.send_message(user.phone_number, response)
                    logger.debug(f"Reminder successfully sent to user {user.id}")
                    chat_client.add_message(user.id, ASSISTANT_ROLE, message_sent.body, message_sent.sid, reminder_id)
                except Exception as e:
                    logger.error(f"Failed to send message for the user {user.id}: {e}")
            else :
                logger.debug(f"There was a {response} when trying to generate the user's reminder")
                return
                
        except Exception as e:
            logger.error(f"An error occurred while sending a reminder to user: {user.id}\nError: {e}")
            return