import datetime
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func, case

from src.config.logging_config import Logger
from src.data_manager.user import get_user
from src.db_session import session_scope

from .models import Message, User

logger = Logger('myfoodrepo.models.message').get_logger()


def get_user_messages(user_id):
    """
    Retrieves all messages associated with a specified `user_id`, ordered by date & time.

    Args:
        user_id (int): The ID of the user whose messages are being retrieved.

    Returns:
        list: A list of `Message` objects associated with the specified user_id, ordered by date & time.

    """
    with session_scope() as session:
        return session.query(Message).filter_by(user_id=user_id).order_by(Message.datetime).all()

        
def get_study_group_messages(group):
    """
    Retrieves the messages sent for the study group we're interested in.

    Args:
        group (`int`): The study group's number (0,1,2 or 3.)

    Returns:
        list: A `list`, containing all `Message` objects for a specific study group.
    """  

    with session_scope() as session:
        return (
            session.query(Message)
            .join(User, User.id == Message.user_id) 
            .filter(User.study_group == group)  
            .filter(Message.twilio_message_id.isnot(None))
            .all()
        )
    
def get_user_messages_per_hour(): #TODO : Modify this function's name

    """
    Retrieves the count of user messages per hour, for an entire day.

    Args:
        None

    Returns:
        List[dict]: A list of dictionaries, each containing the hour of the day (0-23) and the 
                    count of user messages for that hour.
    """

    with session_scope() as session:
        results = session.query(
            func.extract('hour', Message.datetime).label('hour'),
            func.count(case((Message.role == "user", 1))).label("user_count")
        ).group_by(func.extract('hour', Message.datetime)).order_by(func.extract('hour', Message.datetime)).all()
        
        hour_counts = {int(hour): user_count for hour, user_count in results}
        
        return [
            {"hour": hour, "user_count": hour_counts.get(hour, 0)}
            for hour in range(24)
        ]
    

def get_messages_count_per_day(): #TODO : Modify this function's name to get_daily_messages
    
    """
    Retrieves the count of assistant and user messages per day within the current study span.

    Args:
        None

    Returns:
        List[dict]: A list of dictionaries, each containing the date, the count of assistant messages, 
                    and the count of user messages for that day.
    """

    with session_scope() as session:
        results = session.query(
            func.date(Message.datetime),
            func.count(case((Message.role == "assistant", 1))).label("assistant_count"),
            func.count(case((Message.role == "user", 1))).label("user_count")
        ).group_by(func.date(Message.datetime)).order_by(func.date(Message.datetime)).all()
        
        date_counts = {str(date): {"assistant_count": assistant_count, "user_count": user_count} for date, assistant_count, user_count in results}

        #We retrieve the beginning and end date, to allow for "0" values at dates where no data was obtained.
        if results:
            start_date = results[0][0]
            end_date = results[-1][0]

            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            all_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_date - start_date).days + 1)]
            logger.debug(f"🟢 Retrieving the daily user / assistant messages count in between {start_date} & {end_date}")
        else:
            logger.debug(f" No daily user / assistant messages data to retrieve")
            all_dates = []


        return [
             {"date": date, "assistant_count": date_counts.get(date, {"assistant_count": 0, "user_count": 0})["assistant_count"],
              "user_count": date_counts.get(date, {"assistant_count": 0, "user_count": 0})["user_count"]}
             for date in all_dates
         ]
    
def get_messages_count_per_day_per_study_group(): #TODO : Use the get_messages_count_per_day to code this function, code duplication otherwise.
    """
    Retrieves the count of messages sent by users for each study group per day.

    Returns:
        dict: A dictionary where the key is the study group number, and the value is a list of dictionaries
              containing the date and user message count for that study group.
    """
    with session_scope() as session:

        #We Query to count the number of messages per study group per day.
        results = session.query(
            func.date(Message.datetime).label('date'),
            User.study_group,
            func.count(case((Message.role != "system", 1))).label('user_count')
        ).join(User, User.id == Message.user_id) \
        .filter(Message.role != "system")  \
        .group_by(func.date(Message.datetime), User.study_group)\
        .order_by(func.date(Message.datetime), User.study_group)\
        .all()
        
        study_group_messages = defaultdict(dict)
        #We retrieve the beginning and end date, to allow for "0" values at dates where no data was obtained.
        if results:
            start_date = results[0][0]
            end_date = results[-1][0]

            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            all_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_date - start_date).days + 1)]
            logger.debug(f"🟢 Retrieving the daily & per study group user / assistant messages count in between {start_date} & {end_date}")
        else:
            logger.debug(f" No daily & per study group user / assistant messages data to retrieve")
            all_dates = []

        for date, study_group, user_count in results:
            date_str = str(date)
            if study_group not in study_group_messages:
                study_group_messages[study_group] = {d: 0 for d in all_dates} 
            study_group_messages[study_group][date_str] = user_count
        
        return {
            study_group: [{"date": date, "user_count": user_count} for date, user_count in sorted(messages.items())]
            for study_group, messages in study_group_messages.items()
        }



def get_all_messages(filter_twilio_message_id=None, filter_assistant_messages = False):
    """
    Retrieves all messages within the database. Optionally filters out messages that have not been sent / received

    Args:
        filter_twilio_message_id (bool or None): If True, only retrieves messages where twilio_message_id is not None.

    Returns:
        list: A list of `Message` objects from the database, optionally filtered by twilio_message_id.
    """
    with session_scope() as session:
        
        if filter_twilio_message_id:
            logger.debug(f"🟢 Retrieving all messages having a Twilio Message ID")
            return session.query(Message).filter(Message.twilio_message_id != None).all()
        elif filter_assistant_messages:
            logger.debug(f"🟢 Retrieving all users & assitant messages")
            return session.query(Message).filter(Message.role != "system").all()
        else:
            logger.debug(f"🟢 Retrieving all messages in the database")
            return session.query(Message).all()
        

def get_study_start_date():
    """ 
    Retrieves the date at which the study officially started, using the first welcome message.

    returns:
        datetime: The datetime object at which the study started.
    """

    all_messages = get_all_messages(filter_twilio_message_id=True)
    if not all_messages:
        return None 

    relevant_messages = [msg for msg in all_messages if "MyFoodRepo" in msg.content]
    if not relevant_messages:
        return None 

    earliest_message = min(relevant_messages, key=lambda msg: msg.datetime)
    return earliest_message.datetime



def db_add_message(user_id, role, content, twilio_message_id,reminder_id):
    """
    Adds a message to the conversation history in the database.

    Args:
        user_id (int): The ID of the user.
        role (str): The role of the message (e.g., "user", "assistant").
        content (str): The content of the message.
        reminder_id (str): if the message is a reminder, link it to the reminder's ID.

    Returns:
        None
    """
    logger.info(f"🟢 db_add_message() called for user {user_id} with role {role}")
    

    if user_id is None:
        logger.error("🛑 Attempted to insert a message with user_id=None!")
        return

    with session_scope() as session:
        logger.info(f"Prepared to insert message for user: {user_id}, with role: {role}\n")
        message = Message(user_id=user_id, role=role, content=content, twilio_message_id=twilio_message_id,reminder_id=reminder_id)
        session.add(message)   

def db_add_message_from_phone_number(phone_number, role, content, twilio_message_id,reminder_id):

    """
    Adds a message to the database for a user identified by their phone number.

    Args:
        phone_number (str): The phone number of the user to whom the message will be sent.
        role (str): The role of the sender of the message (e.g., "user", "admin").
        content (str): The content of the message being sent.

    Returns:
        tuple: A message string and an HTTP status code:
            - ("User not found", 404) if the user is not found.
            - ("Message Sent with NO errors", 200) if the message is successfully added.

    """

    user = get_user(phone_number)
    if not user:
        logger.error(f"🛑 Did not find a user with phone number {phone_number}")
        return "User not found", 404
    db_add_message(user.id, role, content, twilio_message_id,reminder_id)

    return "Message Sent with NO erros", 200


def checking_message_sanity():
    """
    Performs several sanity checks on the Messages table.
    Outputs a dict mapping problem types to {meal_id: user_id}.

    Returns:
        dict: Problem_type -> {meal_id: user_id}.
    """
    
    
    with session_scope() as session:
        messages = session.query(Message).all()

    now = datetime.now()

    missing_fields = {}
    assistant_missing_twilio_id = {}
    future_timestamps = {}
    missing_timestamps = {}
    twilio_id_map = defaultdict(list)

    for msg in messages:
        # Missing user_id, role or conten
        if not msg.user_id or not msg.role or not msg.content:
            missing_fields[msg.id] = msg.user_id

        # Assistant messages missing Twilio ID
        if msg.role == "assistant" and not msg.twilio_message_id:
            assistant_missing_twilio_id[msg.id] = msg.user_id

        # Future timestamps
        if msg.datetime and msg.datetime > now:
            future_timestamps[msg.id] = msg.user_id

        # Missing timestamps
        if not msg.datetime:
            missing_timestamps[msg.id] = msg.user_id

        # Map Twilio IDs
        if msg.twilio_message_id:
            twilio_id_map[msg.twilio_message_id].append(msg.id)

    # Detect duplicate Twilio IDs
    duplicate_twilio_ids = {twilio_id: ids for twilio_id, ids in twilio_id_map.items() if len(ids) > 1}

    return {
        "missing_fields": missing_fields,
        "assistant_missing_twilio_id": assistant_missing_twilio_id,
        "future_timestamps": future_timestamps,
        "missing_timestamps": missing_timestamps,
        "duplicate_twilio_ids": duplicate_twilio_ids
    }
