# src/utils/csv_utils.py

from typing import Optional

import pandas as pd
from pandas import DataFrame
import json


def read_csv_to_dataframe(file_path) -> Optional[DataFrame]:
    """
    Reads a CSV file and returns a pandas DataFrame.

    Parameters:
    - file_path (str): The path to the CSV file.

    Returns:
    - pd.DataFrame: A pandas DataFrame containing the data from the CSV file.
    """

    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    

def messages_to_dataframe(messages):
    """
    Converts a list of Message objects to a pandas DataFrame.

    Parameters:
    - messages (List[Message]): List of Message objects.

    Returns:
    - pd.DataFrame: DataFrame containing message data from the database.
    """
    data = []
    for msg in messages:
        data.append({
            "id": msg.id,
            "user_id": msg.user_id,
            "role": msg.role,
            "content": msg.content,
            "datetime": msg.datetime,
            "twilio_message_id": msg.twilio_message_id,
            "reminder_id": msg.reminder_id
        })
    return pd.DataFrame(data)


def meals_to_dataframe(meals) -> pd.DataFrame:
    """
    Converts a list of Meal objects to a pandas DataFrame.

    Parameters:
    - meals (List[Meal]): List of Meal objects.

    Returns:
    - pd.DataFrame: DataFrame containing meal data.
    """
    data = []
    for meal in meals:
        data.append({
            "id": meal.id,
            "user_id": meal.user_id,
            "description": meal.description,
            "nutrients": json.dumps(meal.nutrients),
            "food_ids": json.dumps(meal.food_ids),
            "eaten_quantities": json.dumps(meal.eaten_quantities),
            "datetime": meal.datetime
        })
    return pd.DataFrame(data)


def users_to_dataframe(users) -> pd.DataFrame:
    """
    Converts a list of User objects to a pandas DataFrame.

    Parameters:
    - users (List[User]): List of User ORM objects.

    Returns:
    - pd.DataFrame: DataFrame containing user data.
    """
    data = []
    for user in users:
        data.append({
            "phone_number": user.phone_number,
            "myfoodrepo_key": user.myfoodrepo_key,
            "gender": user.gender,
            "age": user.age,
            "language": user.language,
            "diet_preference": user.diet_preference,
            "diet_goal": user.diet_goal,
            "study_group": user.study_group,
            "last_meal_log": user.last_meal_log,
            "withdrawal": user.withdrawal
        })
    return pd.DataFrame(data)
