from datetime import datetime
import pytz

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """
    Represents a user in the database.

    This class defines the structure of the `users` table in the database, which contains information
    about each user, including personal details, dietary preferences, and associated data such as meals,
    reminders, and messages.

    Attributes:
        id (int): The unique identifier for the user (Primary Key).
        phone_number (str): The phone number of the user (unique and non-nullable).
        myfoodrepo_key (str): A unique key associated with the user's participation in MyFoodRepo.
        gender (str): The gender of the user (optional).
        age (int): The age of the user (optional).
        language (str): The preferred language of the user (optional).
        diet_preference (str): The diet preference of the user (optional).
        diet_goal (str): The dietary goal of the user (optional).
        study_group (int): The user's assigned study group (optional).
        reminders (relationship): The reminders associated with the user (one-to-many relationship).
        meals (relationship): The meals associated with the user (one-to-many relationship).
        messages (relationship): The messages associated with the user (one-to-many relationship).

    Methods:
        __init__(self, phone_number, myfoodrepo_key, **kwargs):
            Initializes a new User instance with the provided phone number and MyFoodRepo key, and optional additional attributes.

    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    myfoodrepo_key = db.Column(db.String(50), unique=True)
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    language = db.Column(db.String(10))
    diet_preference = db.Column(db.String(50))
    diet_goal = db.Column(db.String(50))
    study_group = db.Column(db.Integer)
    last_meal_log = db.Column(db.DateTime)
    reminders = db.relationship('Reminder', backref='user', lazy=True)
    withdrawal = db.Column(db.Boolean, default = False)
    study_ended = db.Column(db.Boolean, default = False)
    meals = db.relationship('Meal', backref='user', lazy=True)
    messages = db.relationship('Message', backref='user', lazy=True)

    def __init__(self, phone_number, myfoodrepo_key, **kwargs):
        super().__init__(**kwargs)
        self.phone_number = phone_number
        self.myfoodrepo_key = myfoodrepo_key

    def to_dict(self):
        return {
            "id": self.id,
            "phone_nb": self.phone_number
        }


class Reminder(db.Model):
    """
    Represents a reminder for a user related to their meal schedule.

    This class defines the structure of the `reminders` table in the database, which stores reminder data 
    for users, including the time of the reminder and the associated meal type (e.g., breakfast, lunch, etc.).

    Attributes:
        id (int): The unique identifier for the reminder (Primary Key).
        user_id (int): The foreign key linking to the user who owns the reminder (references `users.id`).
        time (datetime.time): The time at which the reminder should trigger.
        meal_type (str): The type of meal associated with the reminder (e.g., "breakfast", "lunch", etc.).

    Constraints:
        unique_user_meal_type (UniqueConstraint): Ensures that each user can only have one reminder per meal type.

    Methods:
        __init__(self, user_id, time, meal_type):
            Initializes a new Reminder instance with the provided user ID, time, and meal type.

    """
    __tablename__ = 'reminders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    time = db.Column(db.Time, nullable=False)
    meal_type = db.Column(db.String(50))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'meal_type', name='unique_user_meal_type'),
    )

    def __init__(self, user_id, time, meal_type):
        self.user_id = user_id
        self.time = time
        self.meal_type = meal_type


class Meal(db.Model):

    """
    Represents a meal consumed by a user.

    This class defines the structure of the `meals` table in the database, which stores information 
    about meals including the user who consumed the meal, a description of the meal, its nutritional 
    information (nutrients), and the datetime when the meal was consumed.

    Attributes:
        id (int): The unique identifier for the meal (Primary Key).
        user_id (int): The foreign key linking to the user who consumed the meal (references `users.id`).
        description (str): A description of the meal (e.g., "Chicken Salad").
        nutrients (dict): A JSON object containing the meal's nutritional information, typically including calories, protein, fat, etc.
        datetime (datetime): The datetime when the meal was consumed (defaults to the current UTC time).

    Methods:
        __init__(self, user_id, description, nutrients, datetime):
            Initializes a new Meal instance with the provided user ID, description, nutrients, and datetime.

    """
    __tablename__ = 'meals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.String(255))
    nutrients = db.Column(db.JSON)
    food_ids = db.Column(db.JSON)
    eaten_quantities = db.Column(db.JSON)
    datetime = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, description, nutrients, food_ids, eaten_quantities, datetime):
        self.user_id = user_id
        self.description = description
        self.nutrients = nutrients
        self.food_ids = food_ids
        self.datetime = datetime
        self.eaten_quantities = eaten_quantities

def get_swiss_time():
    tz = pytz.timezone('Europe/Zurich')
    return datetime.now(tz)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(255))
    content = db.Column(db.String(255))
    datetime = db.Column(db.DateTime, default=get_swiss_time)
    twilio_message_id = db.Column(db.String(255), unique=True, nullable=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'), nullable=True)  
    

    def __init__(self, user_id, role, content, twilio_message_id, reminder_id=None):
        self.user_id = user_id
        self.role = role
        self.content = content
        self.twilio_message_id = twilio_message_id
        self.reminder_id = reminder_id
