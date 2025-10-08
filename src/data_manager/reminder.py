from datetime import datetime

from src.config.logging_config import Logger
from src.db_session import session_scope
from collections import defaultdict

from .models import Reminder, User, Message

logger = Logger('myfoodrepo.models.reminder').get_logger()

def get_user_reminders(user):
    """
    Retrieves the reminders sent for the specified user.

    Args:
        user: `user` object for which we aim to retrieve reminders.

    Returns:
        list: A `list`, containing all `Reminder` objects for a user in the database
    """

    with session_scope() as session:
        logger.info(f"Retrieving the reminders for user {user.id}")
        return session.query(Reminder).filter_by(user_id=user.id).order_by(Reminder.time).all() # type: ignore
    
def get_previous_reminder_texts(user, limit=10):
    """
    Retrieves and formats the last `limit` reminder messages sent to the user.

    Args:
        user: The `user` object.
        limit (int): Maximum number of past reminders/messages to include.

    Returns:
        str: A formatted string listing past reminder messages, ordered from newest to oldest.
    """
    with session_scope() as session:
        logger.info(f"Retrieving the reminder messages for user {user.id}")
        
        reminders_with_messages = (
            session.query(Reminder, Message)
            .join(Message, Reminder.id == Message.reminder_id)
            .filter(Reminder.user_id == user.id)
            .order_by(Message.datetime.desc())
            .limit(limit)
            .all()
        )

        if not reminders_with_messages:
            return "No previous reminders."

        reminders = [f"- {message.content.strip()}\n" for _, message in reminders_with_messages]

        return "\n".join(reminders)
    

def get_study_group_reminders(group):
    """
    Retrieves the reminders sent for the study group we're interested in.

    Args:
        group (`int`): The study group's number (0,1,2 or 3.)

    Returns:
        list: A `list`, containing all `Reminder` objects for a specific study group.
    """  

    with session_scope() as session:
        logger.info(f"Retrieving the reminders for study group {group}")
        return (
            session.query(Reminder)
            .join(User, User.id == Reminder.user_id)  # type: ignore
            .filter(User.study_group == group)  
            .all()
        )
    
def get_all_reminders():
    """
    Retrieves the reminders for all users in the cohort.

    Args :
        None

    Returns:
        list : A list, containing all `Reminder` objects in the database. 
    """
    with session_scope() as session:
        logger.info(f"Retrieving all reminders in the database")
        return session.query(Reminder).all()
    
def add_reminder(user_id, time, meal_type):
    """
    Creates and stores a new reminder for a specific user, time and meal type.

    Args:
        user_id (int): The unique identifier of the user.
        time (str): The time for the reminder (in 'HH:MM' format).
        meal_type (str): The type of meal (e.g 'breakfast', 'lunch'...)

    Returns:
        tuple: A response message and a HTTP status code.
    
    """
    with session_scope() as session:
        try:
            t = datetime.strptime(time, '%H:%M').time()
            existing_reminder = session.query(Reminder).filter_by(user_id=user_id,meal_type=meal_type).first()

            if existing_reminder :
                return "There is already an existing reminder for this user & meal type.", 400
            else:
                new_reminder = Reminder(user_id=user_id,
                                    time=t,
                                    meal_type=meal_type)

                session.add(new_reminder)
                logger.info(f"Prepared to add a {meal_type} reminder for user:{user_id}")
                return "Reminder added", 200
        except Exception as e:
            logger.error(f"Failed to add reminder: {user_id}\nError: {e}")
            return "Error adding reminder", 500

def remove_reminder(reminder_id) :
    """
    Removes a reminder by its ID.

    Args:
        reminder_id (int): The unique identifier of the reminder to be removed.

    Returns:
        --.
    """

    with session_scope() as session:
        try:
            reminder = session.query(Reminder).filter_by(id=reminder_id).first()

            if reminder:
                session.delete(reminder)
                logger.info(f"Removed reminder with ID: {reminder_id}")
                return "Reminder removed", 200
            else:
                logger.warning(f"Reminder with ID {reminder_id} not found")
                return "Reminder not found", 404

        except Exception as e:
            logger.error(f"Failed to remove reminder {reminder_id}.\nError: {e}")
            return "Error removing reminder", 500



def add_reminder_all_users():
    """
    Adds meal reminders for all eligible users in the system. Users in 
    study groups 0 and 2 are thus skipped.

    Reminders are only added if the user does not already have existing ones.
    
    Returns:
        None
    """
    logger.info("Adding reminders for all users in the system...")
    all_users = User.query.all()

    for user in all_users:
        if user.study_group == 0 or user.study_group == 2:
            logger.debug(f"Skipping user: {user.id} since their study group does not include it as a feature")
            continue
        if user.study_ended:
            logger.debug(f"Skipping user {user.id}, as study has ended for them.")
            continue
        existing_reminders_count = Reminder.query.filter_by(user_id=user.id).count()
        if existing_reminders_count > 0:
            logger.debug(f"Skipping user: {user.id} reminders already added")
            continue

        add_reminder(user.id, "07:00", "Breakfast")
        add_reminder(user.id, "12:00", "Lunch") 
        add_reminder(user.id, "19:00", "Dinner")
    logger.info("Adding reminders DONE.")


def reminders_check():

    """
    Checks for missing meal reminders for users in specific study groups.

    This function queries a database to find users in study groups 1 and 3 who have set meal reminders
    (for breakfast, lunch, or dinner). It then checks for missing reminders for each user to obtain a
    a dictionary of users with the specific missing meal reminders.

    Returns:
        dict: A dictionary where the keys are user IDs and the values are lists of missing meal reminders 
              (e.g., ["breakfast", "lunch"]).
    """

    with session_scope() as session:
        
        reminders = (
            session.query(User.id, User.study_group, User.study_ended, Reminder.meal_type)
            .outerjoin(Reminder, Reminder.user_id == User.id)  
            .all()  
        )

        missing_reminders = {}  

        user_reminders = {}
        for user_id, study_group, study_ended, reminder_type in reminders: 
            if not study_ended :   
                if study_group in {1, 3}:
                    if user_id not in user_reminders:
                        user_reminders[user_id] = set()  
                    if reminder_type and reminder_type.lower() in {"breakfast", "lunch", "dinner"}:
                        user_reminders[user_id].add(reminder_type.lower())  

        all_reminders = {"breakfast", "lunch", "dinner"}
        for user_id in user_reminders:
            if not study_ended :  
                logger.info(f"Retrieving any missing reminders for user {user_id}")
                missing = all_reminders - user_reminders[user_id] 
                if missing: 
                    logger.info(f"Found the following missing reminders for user {user_id} : {missing}")
                    missing_reminders[user_id] = list(missing)

        users_with_no_reminders = set(User.id for User in session.query(User.id).filter(User.study_group.in_([1, 3]), User.study_ended == False).all()) - set(user_reminders.keys())
        for user_id in users_with_no_reminders:
            logger.info(f"User {user_id} does not have any reminders in the database")
            missing_reminders[user_id] = ["breakfast", "lunch", "dinner"]

        return missing_reminders

from datetime import datetime

def checking_reminders_sanity():
    """
    Performs soft checks on the Reminder table to identify potential issues:
    - Missing critical fields: user_id, time, meal_type
    - Duplicate reminders: Same user and meal type at the same time
    - Invalid meal types
    - Invalid reminder times

    Returns:
        dict: Dictionary containing findings for each type of soft check.
    """

    with session_scope() as session:
        reminders = session.query(Reminder).all()

    missing_fields = {}
    duplicate_reminders = defaultdict(list)
    invalid_meal_types = {}
    invalid_times = {}

    valid_meal_types = {"breakfast", "lunch", "dinner"}

    for reminder in reminders:
        # 1. Check if we miss any critical field
        if not reminder.user_id or not reminder.time or not reminder.meal_type:
            missing_fields[reminder.id] = {
                "user_id": reminder.user_id,
                "time": reminder.time,
                "meal_type": reminder.meal_type
            }

        #2. Check for any invalid meal types
        if reminder.meal_type and reminder.meal_type.lower() not in valid_meal_types:
            invalid_meal_types[reminder.id] = reminder.meal_type

        #3. Check for any invalid reminder times
        try:
            reminder_time = datetime.strptime(str(reminder.time), "%H:%M:%S")
        except ValueError:
            invalid_times[reminder.id] = reminder.time

        #4. Check for any duplicate reminders (same user, same meal type, same time)
        duplicate_count = session.query(Reminder).filter_by(
            user_id=reminder.user_id,
            meal_type=reminder.meal_type,
            time=reminder.time
        ).count()

        if duplicate_count > 1:
            duplicate_reminders[reminder.user_id].append({
                "meal_type": reminder.meal_type,
                "time": reminder.time
            })

    return {
        "missing_fields": missing_fields,
        "duplicate_reminders": duplicate_reminders,
        "invalid_meal_types": invalid_meal_types,
        "invalid_times": invalid_times
    }
