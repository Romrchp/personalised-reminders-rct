from collections import Counter

from src.config.logging_config import Logger
from src.db_session import session_scope

from .models import User

logger = Logger('myfoodrepo.models.user').get_logger()


def get_user(phone_number):
    """
    Retrieves a user using their phone number.

    Args:
        phone_number (str): The phone number of the user.

    Returns:
        User: The User object if found, otherwise None.
    
    """
    with session_scope() as session:
        user = session.query(User).filter_by(phone_number=phone_number).first()
        
        if user:
            logger.info(f"User found: {user}")
        else:
            logger.warning(f"User NOT found for phone number: {phone_number}")
        
        return user

def get_users_by_study_group(study_group, page=1, per_page=None):
    """
    Retrieves users belonging to a specific study group.

    Args:
        study_group (int): The study group to filter users by.
        page (int): Page number for pagination.
        per_page (int): Number of users per page.

    Returns:
        Pagination object: Paginated users list.
    """
    with session_scope() as session:
        return(
            session.query(User)
            .filter_by(study_group=study_group)
            .all()
        )
    
def get_age_distribution(study_group=None):
    """
    Retrieves the age distribution of users, optionally filtered by study group.
    """
    with session_scope() as session:
        query = session.query(User.age)
        if study_group is not None:
            query = query.filter(User.study_group == study_group)
        ages = [age for (age,) in query.all() if age is not None]
        return dict(Counter(ages))


def get_gender_distribution(study_group=None):
    """
    Retrieves the gender distribution of users, optionally filtered by study group.
    """
    with session_scope() as session:
        query = session.query(User.gender)
        if study_group is not None:
            query = query.filter(User.study_group == study_group)
        genders = [gender for (gender,) in query.all() if gender]
        return dict(Counter(genders))
    

def get_language_distribution(study_group=None):
    """
    Retrieves the language preference distribution of users, optionally filtered by study group.
    """
    with session_scope() as session:
        query = session.query(User.language)
        if study_group is not None:
            query = query.filter(User.study_group == study_group)
        languages = [lang for (lang,) in query.all() if lang]
        return dict(Counter(languages))
    
def get_started_users_per_group():
    """
    Retrieves, per study group, the number of registered users that have started using the application.

    Returns: 
        dict: A dictionary with the study group as the key, and a value pair of the number of "has used" and "never used".
    """
    study_groups = [0, 1, 2, 3]
    active_inactive_dict = {}
    for group in study_groups:
        curr_group_users = get_users_by_study_group(group)
        started = sum(1 for user in curr_group_users if user.last_meal_log is not None)
        not_started = len(curr_group_users) - started
        active_inactive_dict[group] = (started, not_started)

        
    return active_inactive_dict


 
def get_all_users():
    """
    Retrieves all users from the database.

    Returns:
        List[User]: A list of all users.
    """
    return User.query.all()


def is_user_registered(phone_number):
    """
    Verifies if a user in the database is associated to the phone number given.

    Args:
        phone_number (str): The phone number of the user.

    Returns:
        bool: True if the user exists, False otherwise.
    """
    user = get_user(phone_number)
    return user is not None


def is_user_allowed_to_chat(phone_number):
    """
    Verifies if a user is allowed to chat, based on their study group.

    Args:
        phone_number (str): The phone number of the user.

    Returns:
        bool: True if the user is part of group 2 or 3, False otherwise.
    
    """
    user = get_user(phone_number)

    if user.withdrawal:
        return False, "User has withdrawn"
    
    if user.study_ended:
        return False, "Study has ended for the user"

    if user.study_group in [2, 3]:
        return True, "User is in allowed study group"

    return False, "User is not in an allowed study group"


def add_user_tmp(user: User):
    """
    Adds a temporary user to the database.

    Args:
        user (User): The User object to be added to the database.

    Returns:
        tuple: A tuple containing a message string and an HTTP status.
    
    """
    with session_scope() as session:
        try:
            session.add(user)
            logger.info(f"Prepared to insert user with phone number: {user.phone_number}")
            return "User added", 200
        except Exception as e:
            logger.error(f"Failed to insert user:: {user.phone_number}\n Error: {e}")
            return "Error adding user", 500

def detect_user_participation_change(from_number,body, opt_in_keywords, opt_out_keywords):
    """
    Catches a user's message content to either withdraw them from the study, or re-integrate them, if necessary.

    Args:
        from_number(str): The phone number of the user
        body(str) : The content of the message the user sent towards our chatbot. 
        opt_in_keywords : A list containing the opt-in keywords for our study.
        opt_out_keywords : A list containing the opt-out keywords for our study.

    Returns:
        (bool,bool) : A first boolean to indicate if participation changes, a second one to indicate
                      if it's for withdrawal(true) or reintegration(false)
    """

    if body.lower() in [keyword.lower() for keyword in opt_in_keywords] :
        logger.info(f"User with phone number {from_number} sent {body} : re-integrating them to our pool.")
        return True, False

    if body.lower() in [keyword.lower() for keyword in opt_out_keywords] :
        logger.info(f"User with phone number {from_number} sent {body} : withdrawing them from our pool.")
        return True, True

    else :
        return False, False
    
def update_user_participation(phone_number, withdrawal_status):
    """
    Updates the participation status (withdrawal attribute) of a user.

    Args:
        phone_number (str): The phone number of the user whose status is to be updated.
        withdrawal_status (bool): True to withdraw the user, False to re-integrate the user.

    Returns:
        tuple: A tuple containing a message string and an HTTP status code.
    """
    with session_scope() as session:
        try:
            user = session.query(User).filter_by(phone_number=phone_number).first()
            if not user:
                logger.error(f"No user found with phone number: {phone_number}")
                return "User not found", 404

            user.withdrawal = withdrawal_status
            session.commit()
            logger.info(f"Updated withdrawal status for user {phone_number} to {withdrawal_status}")
            return "User participation status updated", 200
        except Exception as e:
            logger.error(f"Failed to update participation status for user {phone_number}\nError: {e}")
            return "Error updating user participation status", 500

def update_user_study_end(phone_number, end_status):
    """
    Updates the participation status (withdrawal attribute) of a user.

    Args:
        phone_number (str): The phone number of the user whose status is to be updated.
        withdrawal_status (bool): True to withdraw the user, False to re-integrate the user.

    Returns:
        tuple: A tuple containing a message string and an HTTP status code.
    """
    with session_scope() as session:
        try:
            user = session.query(User).filter_by(phone_number=phone_number).first()
            if not user:
                logger.error(f"No user found with phone number: {phone_number}")
                return "User not found", 404

            user.study_ended = end_status
            session.commit()
            logger.info(f"Updated ending status for user {phone_number} to {end_status}")
            return "User participation status updated", 200
        except Exception as e:
            logger.error(f"Failed to update ending status for user {phone_number}\nError: {e}")
            return "Error updating user participation status", 500



def add_user(phone_number, participation_key):

    """
    Adds a new user to the database with the provided phone number & participation key.

    Args:
        phone_number(str): The phone number of the user to be added
        participation_key (str): The participation key associated with the user.
    
    Returns:
        tuple: A tuple containing a message string and a HTTP status.
    
    """
    with session_scope() as session:
        try:
            new_user = User(phone_number=phone_number,
                            myfoodrepo_key=participation_key,
                            language='en',
                            study_group=3)
            
            session.add(new_user)
            logger.info(f"Prepared to insert user with phone number: {new_user.phone_number}")
            return "User Added", 200
        except Exception as e:
            logger.error(f"Failed to insert user: {new_user.phone_number} due to {e}")
            return "Error Adding User", 500


def delete_user(phone_number):
    """
    Delete a user from the database, using their phone number.

    Args:
        phone_number (str): The phone number of the user to be deleted.

    Returns:
        tuple: A tuple containing a message string and an HTTP status code:
        
    """
    with session_scope() as session:
        try:
            user = session.query(User).filter_by(phone_number=phone_number).first()
            if not user:
                logger.error(f"No user found with phone number: {phone_number}")
                return "User not found", 404

            session.delete(user)
            logger.info(f"Prepared to delete user with phone number: {phone_number}")
            return "User deleted", 200
        except Exception as e:
            logger.error(f"Failed to delete user with: {phone_number}\nError: {e}")
            return "Error deleting user", 500


def checking_users_sanity():
    """
    Performs soft checks on the User table to identify potential issues:
    - Users with missing critical fields (phone_number, gender, language, study_group)
    - Users with age outside a realistic range (18 to 90)

    Returns:
        dict: Dictionary containing findings for each type of soft check.
    """
    from collections import defaultdict
    from src.db_session import session_scope
    from .models import User

    with session_scope() as session:
        users = session.query(User).all()

    missing_fields = {}
    unrealistic_ages = {}

    age_min, age_max = 18, 90  

    for user in users:
        if not user.phone_number or not user.gender or not user.language or user.study_group is None:
            missing_fields[user.id] = user.phone_number
        if user.age is not None and (user.age < age_min or user.age > age_max):
            unrealistic_ages[user.id] = user.phone_number

    return {
        "missing_fields": missing_fields,
        "unrealistic_ages": unrealistic_ages
    }
