from datetime import datetime, timedelta
from collections import defaultdict
import random
import json
from flask import session,request
import pandas as pd
import re
from sqlalchemy import func
from sqlalchemy.exc import MultipleResultsFound

from src.config.logging_config import Logger
from src.db_session import session_scope

from .models import Meal, User

logger = Logger('myfoodrepo.models.meal').get_logger()


def get_meal_by_id(meal_id):
    """Retrieves a Meal instance using an id"""
    with session_scope() as session:
        try:
            curr_meal = session.query(Meal).filter(Meal.id == meal_id).one_or_none()
            return curr_meal
        except MultipleResultsFound:
            logger.error(f"Duplicate entries found for meal_id {meal_id}. Fix it !")
            return None

def remove_user_meal(meal_id) :
    """Removes a Meal object from the DB using an id."""
    with session_scope() as session:
       try: 
        curr_meal = get_meal_by_id(meal_id)
        if curr_meal :
            session.delete(curr_meal)
            logger.info(f"Removed meal with ID : {meal_id}")
            return "Meal removed", 200
        else:
            logger.warning(f"Meal with ID {meal_id} not found")
            return "Meal not found", 400
       except Exception as e :
           logger.error(f"Failed to remove meal {meal_id}.\nError: {e}")
           return "Error", 404

def edit_meal_characteristic(meal_id):
        """Edit a Meal object's characteristics, using an id."""
        meal=get_meal_by_id(meal_id)

        if meal :
            meal.description = request.form.get("description")
            meal.user_id = request.form.get("user_id")
            datetime_str = request.form.get("datetime")
            if datetime_str:
                from datetime import datetime
                meal.datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')

            # Nutrients (dictionary of name → value)
            nutrients = request.form.getlist("nutrients")
            for key, value in request.form.items():
                if key.startswith("nutrients["):
                    nutrient_name = key[10:-1]
                    try:
                        meal.nutrients[nutrient_name] = float(value)
                    except ValueError:
                        return "Error"
                    
            return "Information updated"
        
        return "No meal found"

         

def get_most_recent_meal_time(meals_data):
    """
    Extracts the most recent meal timestamp from a verbose meal history log.

    Args:
        meals_data (str): Full-text log of multiple meals, each containing a 'Time:' line.

    Returns:
        datetime: The most recent datetime object found in the log.
    """
    time_strings = re.findall(r"Time:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})", meals_data)
    
    # Convert to datetime
    time_objects = [datetime.strptime(ts, "%Y-%m-%d %H:%M") for ts in time_strings]
    
    if not time_objects:
        return None
    
    return max(time_objects)


def get_nutrient_unit(nutrient_key):
    """Helper function to get the appropriate unit for each nutrient"""
    unit_mapping = {
        "energy_kcal": "kcal",
        "carbohydrates": "g", "protein": "g", "fat": "g",
        "fatty_acids_saturated": "g", "fatty_acids_polyunsaturated": "g",
        "fatty_acids_monounsaturated": "g", "fiber": "g",
        "starch": "g", "sugar": "g", "salt": "g", "alcohol": "g",
        "sodium": "mg", "iron": "mg", "zinc": "mg", 
        "phosphorus": "mg", "calcium": "mg", "cholesterol": "mg",
        "water": "mL"
    }
    return unit_mapping.get(nutrient_key, "")


def get_recent_meals_string_for_user(participation_key, meals_nb=20):
    with session_scope() as session:
        recent_meals = (
            session.query(Meal)
            .join(User)
            .filter(User.myfoodrepo_key == participation_key)
            .order_by(Meal.datetime.desc())
            #.limit(meals_nb)
            .all()
        )

        if not recent_meals:
            return "No recent meals found for this user."

        meals_by_date = defaultdict(list)
        for i, meal in enumerate(recent_meals):
            date_str = meal.datetime.strftime('%Y-%m-%d')
            meals_by_date[date_str].append((i, meal))

        result_lines = []
        
        daily_totals = {}
        
        for date in sorted(meals_by_date.keys(), reverse=True):
            result_lines.append(f"Date: {date}\n")
            
            date_totals = defaultdict(float)
            
            for idx, (i, meal) in enumerate(meals_by_date[date], start=1):
                meal_label = "MOST RECENT" if i == 0 else f"PREVIOUS #{i}"
                timestamp = meal.datetime.strftime('%Y-%m-%d %H:%M')
                description = meal.description
                nutrients = meal.nutrients

                for nutrient, value in nutrients.items():
                    if isinstance(value, (int, float)):
                        date_totals[nutrient] += value

                # Format nutrients
                nutrients_lines = []
                for key, value in nutrients.items():
                    unit = get_nutrient_unit(key)
                    nutrients_lines.append(f"  - {key.capitalize()}: {value} {unit}")

                nutrients_text = "\n".join(nutrients_lines)

                meal_text = (
                    f"Meal #{idx} [{meal_label}]:\n"
                    f"  Time: {timestamp}\n"
                    f"  Description: {description}\n"
                    f"  Nutrients:\n{nutrients_text}\n"
                )
                result_lines.append(meal_text)
            
            daily_totals[date] = dict(date_totals)
            result_lines.append(f"DAILY TOTALS for {date}:")
            for nutrient, total in date_totals.items():
                unit = get_nutrient_unit(nutrient)
                result_lines.append(f"  Total {nutrient}: {total:.1f} {unit}")
            result_lines.append("---\n")

        result_lines.append("\n=== COMPUTATIONAL SUMMARY ===")
        result_lines.append(f"Total tracking days: {len(daily_totals)}")
        
        # weekly/period averages for common nutrients
        if daily_totals:
            avg_nutrients = defaultdict(float)
            for date, totals in daily_totals.items():
                for nutrient, value in totals.items():
                    avg_nutrients[nutrient] += value
            
            num_days = len(daily_totals)
            result_lines.append(f"Average daily intake over {num_days} days:")
            for nutrient, total in avg_nutrients.items():
                avg = total / num_days
                unit = get_nutrient_unit(nutrient)
                result_lines.append(f"  - {nutrient}: {avg:.1f} {unit}/day")
        
        result_lines.append("========================\n")

        return "\n".join(result_lines)

    
def get_df_meals_for_user(participation_key):
    """Retrieves a df containing meals for a certain user, using their participation key."""
    with session_scope() as session :
        user_meals = (session.query(Meal)\
        .join(User)\
        .filter(User.myfoodrepo_key == participation_key)\
        .all())

        if not user_meals:
            columns = ["id", "user_id", "description", "nutrients", "datetime", "food_ids", "eaten_quantities"]
            return pd.DataFrame(columns=columns)


        meals_data = [
    {
        "id": meal.id,
        "user_id": meal.user_id,
        "description": meal.description,
        "nutrients": meal.nutrients,
        "datetime": meal.datetime,
        "food_ids": meal.food_ids,
        "eaten_quantities": meal.eaten_quantities
    }
    for meal in user_meals
        ]


    users_meal_df = pd.DataFrame(meals_data)
    return(users_meal_df)


def get_meals_per_study_group():
    """
    Retrieves the number of meals logged for each study group.

    Returns:
        dict: A dictionary where the key is the study group identifier (or name), and the value is the count of meals logged by users in that study group.
    """
    with session_scope() as session:
        study_group_meals = session.query(
            User.study_group,  
            func.count(Meal.id).label("meal_count")
        ).join(Meal, Meal.user_id == User.id) \
         .group_by(User.study_group) \
         .all()
        
        meals_per_study_group = {}
        for study_group, meal_count in study_group_meals:
            meals_per_study_group[study_group] = meal_count

        return meals_per_study_group      
    

def get_meals_per_day_per_study_group():
    """
    Retrieves the number of meals logged per day for each study group.

    Returns:
        dict: A dictionary where the key is the study group identifier (or name), 
              and the value is another dictionary where the key is the date and 
              the value is the count of meals logged on that day.
    """
    with session_scope() as session:
        study_group_daily_meals = session.query(
            User.study_group, 
            func.date(Meal.datetime).label('meal_date'),
            func.count(Meal.id).label("meal_count")
        ).join(Meal, Meal.user_id == User.id) \
         .group_by(User.study_group, func.date(Meal.datetime)) \
         .order_by(User.study_group, 'meal_date') \
         .all()
        
        meals_per_day_per_study_group = defaultdict(lambda: defaultdict(int))
        
        if study_group_daily_meals:
            start_date = study_group_daily_meals[0][1]
            end_date = study_group_daily_meals[-1][1]

            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')

            all_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_date - start_date).days + 1)]
        else:
            all_dates = []
        
        for study_group, meal_date, meal_count in study_group_daily_meals:
            meals_per_day_per_study_group[study_group][str(meal_date)] = meal_count
        
        return {
            study_group: [{"date": date, "meal_count": meals_per_day_per_study_group[study_group].get(date, 0)} for date in all_dates]
            for study_group in meals_per_day_per_study_group
        }

def get_all_meals(datetime_sort=False):
    """retrieve all meals in the DB."""
    with session_scope() as session:
        if datetime_sort is False :
            return session.query(Meal).all()
        elif datetime_sort is True :
            return session.query(Meal).order_by(Meal.datetime.desc()).all()

#def get_random_meal_datetime(date, meal_description):
#
#    """
#    Generates a random meal datetime for a given date and meal description based on predefined meal times.
#
#    Args:
#        date (str): The date for the meal in 'YYYY-MM-DD' format.
#        meal_description (str): The description of the meal (e.g., 'Lentil Salad', 'Grilled Chicken & Quinoa Bowl').
#
#    Returns:
#        datetime: A datetime object representing the randomly chosen time for the specified meal on the given date.
#    """
#
#    meal_times = {
#        "Lentil Salad": ["12:00", "19:00"],  
#        "Grilled Chicken & Quinoa Bowl": ["12:00", "19:00"],  
#        "Oatmeal with Almond Butter & Banana": ["07:30", "15:00"],  # Breakfast or Snack
#        "Salmon with Roasted Sweet Potatoes & Spinach": ["19:30"],  # Only Dinner
#        "Tofu Stir-Fry with Brown Rice": ["12:30", "19:00"]  # Lunch or Dinner
#    }
#    
#    chosen_time = random.choice(meal_times[meal_description])
#    meal_datetime = datetime.strptime(date, "%Y-%m-%d").replace(hour=int(chosen_time.split(":")[0]), minute=int(chosen_time.split(":")[1]), second=0, microsecond=0)
#    
#    return meal_datetime
        
def get_cohort_retention():
    """
    Retrieves the cohort retention data, mapping each day to the set of user IDs that logged a meal 
    on that day, within a specific date range.

    Args:
        None

    Returns:
        dict: A dictionary where the keys are dates (in 'YYYY-MM-DD' format) and the values are 
              sets of user IDs who logged meals on that date.
    """

    with session_scope() as session: 
        cohort_data = session.query(
            func.date(Meal.datetime).label("date"),
            Meal.user_id,
            func.count(Meal.id).label("meal_count")
        ).group_by("date", Meal.user_id).all()
        
        retention_dict = defaultdict(set)
        
        if cohort_data:
            start_date = cohort_data[0][0]
            end_date = cohort_data[-1][0]

            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            all_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_date - start_date).days + 1)]
            logger.debug(f"🟢 Retrieving the meal logging activity of users in between {start_date} & {end_date}")

        else:
            logger.debug(f" No activity to retrieve.")
            all_dates = []
        
        for date, user_id, count in cohort_data:
            retention_dict[str(date)].add(user_id)
        
        return {date: retention_dict.get(date, set()) for date in all_dates}

def get_meal_logging_frequency():
    """
    Retrieves the frequency of meal logs per user for each day within the current study span.

    Args:
        None

    Returns:
        dict: A dictionary where the keys are dates (in 'YYYY-MM-DD' format) and the values are 
              dictionaries that map user IDs to the count of meals logged on that date.
    """

    with session_scope() as session :
        meal_logs = session.query(
            func.date(Meal.datetime).label("date"),
            Meal.user_id,
            func.count(Meal.id).label("meal_count")
        ).group_by("date", Meal.user_id).order_by("date").all()

        meal_log_dict = defaultdict(lambda: defaultdict(int))

        if meal_logs:
            start_date = meal_logs[0][0]
            end_date = meal_logs[-1][0]

            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')

            all_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_date - start_date).days + 1)]
            logger.debug(f"🟢 Retrieving the frequency of meal logs, per user, in between {start_date} & {end_date}")
        else:
            logger.debug(f" No logging meal frequency data to retrieve")
            all_dates = []

        for date, user_id, meal_count in meal_logs:
            meal_log_dict[str(date)][user_id] = meal_count

        return {date: meal_log_dict.get(date, {}) for date in all_dates}


def get_meal_logging_by_hour():
    """
    Retrieves the frequency of meal logs per hour across all days in the current study span.
    
    Args:
        None
        
    Returns:
        dict: A dictionary where keys are hours (0-23) and values are the count of meals 
              logged during that hour across all days.
    """
    
    with session_scope() as session:
        
        meal_logs = session.query(
            func.extract('hour', Meal.datetime).label("hour"),
            func.count(Meal.id).label("meal_count")
        ).group_by("hour").order_by("hour").all()
        
        
        hourly_meals = {hour: 0 for hour in range(24)}
        
        if meal_logs:
            logger.debug(f"🟢 Retrieving meal logging frequency by hour of day")
            
            for hour, meal_count in meal_logs:
                hourly_meals[int(hour)] = meal_count
        else:
            logger.debug(f"📊 No meal logging data to retrieve")
            
        return hourly_meals
    


def add_meals_for_user(user_id):
    """
    Adds test meal entries for a certain user under a tmp time range.

    Args:
        user_id (int): The ID of the user for whom meals are being added.

    Returns:
        tuple: A message string and an HTTP status code, differing on success or failure.
    """
    start_date = datetime(2025, 3, 24)
    end_date = datetime(2025, 4, 13)
    meals = [
        {"description": "Lentil Salad", "nutrients": {"calories": 350, "protein": "25g", "fat": "10g"}},
        {"description": "Grilled Chicken & Quinoa Bowl", "nutrients": {"calories": 450, "protein": "40g", "fat": "12g"}},
        {"description": "Oatmeal with Almond Butter & Banana", "nutrients": {"calories": 380, "protein": "12g", "fat": "14g"}},
        {"description": "Salmon with Roasted Sweet Potatoes & Spinach", "nutrients": {"calories": 500, "protein": "45g", "fat": "18g"}},
        {"description": "Tofu Stir-Fry with Brown Rice", "nutrients": {"calories": 420, "protein": "30g", "fat": "15g"}},
    ]
    
    with session_scope() as session:
        try:
            current_date = start_date
            while current_date <= end_date:
                selected_meals = random.sample(meals, k=2)  
                if random.random() < 0.5:  
                    selected_meals.append(random.choice(meals))
                
                for meal in selected_meals:
                    meal_datetime = get_random_meal_datetime(current_date.strftime("%Y-%m-%d"), meal["description"])
                
                current_date += timedelta(days=1)
            
            return "Meals added successfully", 200
        except Exception as e:
            logger.error(f"An error occurred while adding meals for user: {user_id}\nError: {e}")
            return "Error adding meals", 500
    

def checking_meals_sanity():
    """
    Performs several sanity checks on the Meals table.
    Outputs a dict mapping problem types to {meal_id: user_id}.
    
    Returns:
        dict: Problem_type -> {meal_id: user_id}.
    """


    with session_scope() as session:
        meals = session.query(Meal).all()

        problems = {
                "missing_fields": {},
                "mismatched_ids_quantities": {},
                "energy_mismatch": {},
                "negative_nutrients": {},
                "outlier_eaten_quantity": {},
                "invalid_food_ids": {},
            }

        for meal in meals: 

            meal_id = meal.id
            user_id = meal.user_id if hasattr(meal, "user_id") else None

            #1. Checking if all fields are present.
            if not meal.description or not meal.nutrients or not meal.food_ids or not meal.eaten_quantities:
                problems["missing_fields"][meal_id] = user_id


            if (
                not isinstance(meal.food_ids, dict)
                or not isinstance(meal.eaten_quantities, dict)
                or len(meal.food_ids) != len(meal.eaten_quantities)
                or len(meal.food_ids) == 0
                or len(meal.eaten_quantities) == 0
            ):
                problems["mismatched_ids_quantities"][meal_id] = user_id

            elif meal.nutrients and meal.food_ids and meal.eaten_quantities:

                # 2. If there is an ID mismatch
                if len(meal.food_ids) != len(meal.eaten_quantities) :
                    problems["mismatched_ids_quantities"][meal_id] = user_id

                # 3. Nutritional consistency (15% tolerance)
                fat_kcal = meal.nutrients.get("fat", 0) * 9
                protein_kcal = meal.nutrients.get("protein", 0) * 4
                carbs = meal.nutrients.get("carbohydrates", 0)
                fiber = meal.nutrients.get("fiber", 0)
                                           
                # Net carbs at 4 kcal/g, fiber at ~2 kcal/g
                carbs_kcal = (carbs * 4) + (fiber * 2) if fiber > 0 else carbs * 4
                alcohol_kcal = meal.nutrients.get("alcohol", 0) * 7
                estimated_kcal = fat_kcal + protein_kcal + carbs_kcal + alcohol_kcal
                actual_kcal = meal.nutrients.get("energy_kcal", 0)

                if actual_kcal > 0:
                    if actual_kcal < 100:
                        tolerance = 0.25  
                    elif actual_kcal < 500:
                        tolerance = 0.18  
                    else:
                        tolerance = 0.12 
                        
                    if abs(estimated_kcal - actual_kcal) / actual_kcal > tolerance:
                        problems["energy_mismatch"][meal_id] = user_id



                # 4. No Negative nutrients
                for nutrient, value in meal.nutrients.items():
                    if isinstance(value, (int, float)) and value < 0:
                        problems["negative_nutrients"][meal_id] = user_id
                        break
                    
                # 5. Eaten quantities outliers
                eaten_quantities_sum = sum(meal.eaten_quantities.values())
                if eaten_quantities_sum < 10 or eaten_quantities_sum > 2500:
                    problems["outlier_eaten_quantity"][meal_id] = user_id

                # 6. Good Food ID format
                uuid_pattern = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$", re.I)
                for food_name, food_id in meal.food_ids.items():
                    if not uuid_pattern.match(food_id):
                        problems["invalid_food_ids"][meal_id] = user_id
                        break
                    

    return problems
