from pandas import date_range
from src.data_manager.user import *
from src.data_manager.meal import *

from collections import Counter


def categorize_meal_type(row):
    """
    Categorizing meal based on their consumption time.

    Args:
        row: The  `dataframe` row for which consumption time should be analysed. 

    Returns:
        The meal type (Breakfast, Lunch, Snack, Dinner, or Night Snack).
    """
    
    meal_times = {
        (4, 11): 'breakfast',
        (11, 15): 'lunch',
        (15, 18): 'snack',
        (18, 23): 'dinner',
    }

    hour = row['datetime'].hour

    for (start, end), meal in meal_times.items():
        if start <= hour < end:
            return meal
    return 'night_snack'


def calculate_eating_consistency(user) :
    """
    Computes the logging rate, average meals per day & meal frequency for a specific user.

    Args:
        The `user` object for which the metrics should be computed.
    
    Returns:
        A `dictionnary` containing the consistency metrics.
    
    """
    consistency_metrics = {}
    
    #We retrieve all meals and categorize them by consumption time.
    all_user_meals = get_df_meals_for_user(user.myfoodrepo_key)
    if all_user_meals.empty:
        
        return {
            'logging_rate': 0,
            'avg_meals_per_day': 0,
            'breakfast_frequency': 0,
            'lunch_frequency': 0,
            'snack_frequency': 0,
            'dinner_frequency': 0,
            'night_snack_frequency': 0,
            'current_streak': 0,
            'max_streak': 0
        }


    all_user_meals['meal_type'] = all_user_meals.apply(categorize_meal_type, axis=1)
    unique_log_days = all_user_meals['datetime'].dt.date.unique()
    logging_range = (max(unique_log_days) - min(unique_log_days)).days + 1
    meals_per_day = all_user_meals.groupby(all_user_meals['datetime'].dt.date)['meal_type'].count()

    #Consistency metrics
    consistency_metrics['logging_rate'] = len(unique_log_days) / logging_range
    consistency_metrics['avg_meals_per_day'] = meals_per_day.mean()
    
    #Frequency of each meal type
    meal_types = ['breakfast', 'lunch', 'snack', 'dinner', 'night_snack']
    meal_days = {
        meal: set(all_user_meals[all_user_meals['meal_type'] == meal]['datetime'].dt.date)
        for meal in meal_types
    }
    
    for meal in meal_types:
        if meal in meal_days:
            consistency_metrics[f'{meal}_frequency'] = len(meal_days[meal]) / len(unique_log_days)

    #Computing our streak measurements
    main_meals = {'breakfast', 'lunch', 'dinner','snack','night_snack'}
    main_meal_logs = all_user_meals[all_user_meals['meal_type'].isin(main_meals)]
    main_meal_dates_set = set(sorted(main_meal_logs['datetime'].dt.date.unique()))



    if not main_meal_dates_set:
        consistency_metrics['current_streak'] = 0
        consistency_metrics['max_streak'] = 0
    else:
        # Sort dates for proper iteration
        sorted_dates = sorted(main_meal_dates_set)

        # Find max streak by checking all consecutive sequences
        max_streak = 0
        current_temp_streak = 1

        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                current_temp_streak += 1
            else:
                max_streak = max(max_streak, current_temp_streak)
                current_temp_streak = 1
        max_streak = max(max_streak, current_temp_streak)

        today = pd.to_datetime("today").date()
        most_recent_log = max(main_meal_dates_set)

        current_streak = 0
        if (today - most_recent_log).days <= 1:  # Logged today or yesterday
            # Count backwards from most recent date to find current streak
            current_streak = 1
            check_date = most_recent_log

            while True:
                prev_date = check_date - pd.Timedelta(days=1)
                if prev_date in main_meal_dates_set:
                    current_streak += 1
                    check_date = prev_date
                else:
                    break
                
    consistency_metrics['current_streak'] = current_streak
    consistency_metrics['max_streak'] = max_streak

    return consistency_metrics


def analyse_food_preferences(df) : 
    """

    """
    all_food_items = []
    for food_dict in df['food_ids'] :
        all_food_items.extend(food_dict.keys())

    food_counter = Counter(all_food_items)

    analysis = {
        "top_5_foods": food_counter.most_common(5),
        "least_5_foods": food_counter.most_common()[:-6:-1],
        "unique_food_count": len(food_counter),
        "average_food_per_entry": round(len(all_food_items) / len(df),2),
        "food_frequency_distribution": food_counter
    }

    return analysis



def user_diet_analysis(df, window_days=7, analysis_date=None) :
    """
    Analyzes the user's diet based on their meals logged on the app.

    Args :
        A `dataframe` containing all meals consumed by the user.

    Returns :
        A `dictionnary` with the macronutrient and micronutrient profile of the user.
    
    """

    df_analysis = df.copy()
    df_analysis['datetime'] = df_analysis['datetime'].dt.date

    if analysis_date is None:
        analysis_date = df_analysis['datetime'].max()

    start_date = analysis_date - pd.Timedelta(days=window_days-1)
    df_window = df_analysis[
        (df_analysis['datetime'] >= start_date) & 
        (df_analysis['datetime'] <= analysis_date)
    ]

    analysis = {
        'macronutrient_profile': {}
    }

    if df_window.empty:
        return {
            'macronutrient_profile': {},
            'window_info': {
                'start_date': start_date,
                'end_date': analysis_date,
                'window_days': window_days,
                'actual_days_with_data': 0
            }
        }
    
    analysis = {
        'macronutrient_profile': {}
    }

    daily_nutrients = df_window.groupby('datetime').agg({
        'energy_kcal': 'sum',
        'fat': 'sum',
        'carbohydrates': 'sum',
        'protein': 'sum',
        'fiber': 'sum',
        'sugar': 'sum',
        'salt': 'sum',
        'water': 'sum'
    }).mean()
    
    total_calories = daily_nutrients['energy_kcal']
    fat_calories = daily_nutrients['fat'] * 9
    carb_calories = daily_nutrients['carbohydrates'] * 4
    protein_calories = daily_nutrients['protein'] * 4
    sugar_calories = daily_nutrients['sugar'] * 4
    
    fat_pct = (fat_calories / total_calories * 100) if total_calories > 0 else 0
    carb_pct = (carb_calories / total_calories * 100) if total_calories > 0 else 0
    protein_pct = (protein_calories / total_calories * 100) if total_calories > 0 else 0
    sugar_pct = (sugar_calories / total_calories * 100) if total_calories > 0 else 0
    
    
    analysis['macronutrient_profile'] = {
        'daily_calories': float(total_calories),
        'fat_percentage': float(fat_pct),
        'carb_percentage': float(carb_pct),
        'protein_percentage': float(protein_pct),
        'daily_fiber': float(daily_nutrients['fiber']),
        'daily_sugar': sugar_pct,
        'daily_salt': float(daily_nutrients['salt']),
        'daily_water': float(daily_nutrients['water'])
    }
    
    return analysis

def get_recommended_ranges():
    """Return dictionary of recommended nutritional ranges.
    Data provided by the EFSA: https://multimedia.efsa.europa.eu/drvs/index.htm
    """
    return {
        'f_calories_18_29': {'min': 1900, 'max': 2700, 'unit': 'kcal'},
        'f_calories_30_39': {'min': 1800, 'max': 2600, 'unit': 'kcal'},
        'f_calories_40_49': {'min': 1800, 'max': 2600, 'unit': 'kcal'},
        'f_calories_50_59': {'min': 1800, 'max': 2600, 'unit': 'kcal'},
        'f_calories_60_69': {'min': 1600, 'max': 2300, 'unit': 'kcal'},
        'f_calories_70_79': {'min': 1600, 'max': 2300, 'unit': 'kcal'},

        'm_calories_18_29': {'min': 2300, 'max': 3300, 'unit': 'kcal'},
        'm_calories_30_39': {'min': 2250, 'max': 3200, 'unit': 'kcal'},
        'm_calories_40_49': {'min': 2200, 'max': 3150, 'unit': 'kcal'},
        'm_calories_50_59': {'min': 2000, 'max': 3150, 'unit': 'kcal'},
        'm_calories_60_69': {'min': 2000, 'max': 2900, 'unit': 'kcal'},
        'm_calories_70_79': {'min': 2000, 'max': 2850, 'unit': 'kcal'},

        'calories_80': {'min': 1500, 'max': 3000, 'unit': 'kcal'},

        'fat_pct': {'min': 20, 'max': 35, 'unit': '%'},
        'carb_pct': {'min': 45, 'max': 60, 'unit': '%'},
        'protein_pct': {'min': 10, 'max': 35, 'unit': '%'},
        'fiber': {'min': 25, 'max': 35, 'unit': 'g'},
        'sugar': {'min': 0, 'max': 20, 'unit': '%'},
        'salt': {'min': 0, 'max': 5, 'unit': 'g'}
    }

def get_calorie_range_key(gender, age):
    """
    Determine the appropriate calorie range key based on gender and age.
    
    Args: 
        gender: gender of the user
        age: age of the user
    
    Returns :
        The recommended range for the user.

    """
    if gender not in ["m","f"] :
        return None
    
    gender_prefix = 'm' if gender == 'male' else 'f'
    
    if age < 18:
        return None  # No minors in the study anyways
    elif age >= 80:
        return 'calories_80'
    elif age >= 70:
        return f'{gender_prefix}_calories_70_79'
    elif age >= 60:
        return f'{gender_prefix}_calories_60_69'
    elif age >= 50:
        return f'{gender_prefix}_calories_50_59'
    elif age >= 40:
        return f'{gender_prefix}_calories_40_49'
    elif age >= 30:
        return f'{gender_prefix}_calories_30_39'
    else: 
        return f'{gender_prefix}_calories_18_29'


def check_nutrient_level(value, min_val, max_val, nutrient_name, unit=''):
    """
    Checking whether a certain nutrient value is within the recommended range and return an appropriate message.

    Args:
        - value: The nutrient's intake value
        - min_val: The recommended range's lower bound
        - max_val: The recommended range's upper bound
        - nutrient_name: The nutrient to be evaluated.
        - unit: The unit of the nutrient's value.
    
    """
    if value < min_val:
        return f"{nutrient_name} daily intake is low at {value:.2f}{unit} (recommended: {min_val}-{max_val}{unit})."
    elif value > max_val:
        return f"{nutrient_name} daily intake is high at {value:.2f}{unit} (recommended: {min_val}-{max_val}{unit})."
    else:
        return f"{nutrient_name} daily intake is within the recommended range at {value:.2f}{unit}."



def retrieve_nutritional_information(user):
    """
    High-level function which retrieves nutritional information for a user, by calling various other functions.

    Args :
        - user : The user for which we aim to retrieve nutritional information-

    Returns:
        - A `list` of nutritional information, for that specific user, based on the different parameters evaluated in the function.


    """
    #Setting up necessary variables & formatting our data correctly
    recommended_ranges = get_recommended_ranges()
    
    all_user_meals = get_df_meals_for_user(user.myfoodrepo_key)
    if all_user_meals.empty:
        return ["No diet information available yet."]

    extended_nutrients = all_user_meals['nutrients'].apply(pd.Series)
    all_user_meals = pd.concat([all_user_meals.drop(columns=['nutrients']), extended_nutrients], axis=1)
    
    user_diet = user_diet_analysis(all_user_meals)
    profile = user_diet['macronutrient_profile']
    
    information = []
    
    #Checking if the daily calories of the user fall into the recommended range
    calorie_range_key = get_calorie_range_key(user.gender.lower(), user.age)
    
    if calorie_range_key in recommended_ranges:
        calorie_range = recommended_ranges[calorie_range_key]
        information.append(
            check_nutrient_level(
                profile['daily_calories'],
                calorie_range['min'],
                calorie_range['max'],
                'Calorie',
                ' kcal'
            )
        )
    else :
        information.append("Gender doesn't allow for calories computation.")


    nutrients_to_check = [
        ('fat_percentage', 'fat_pct', 'Fat', '% of calories'),
        ('carb_percentage', 'carb_pct', 'Carbohydrates', '% of calories'),
        ('protein_percentage', 'protein_pct', 'Protein', '% of calories'),
        ('daily_fiber', 'fiber', 'Fiber', 'g'),
        ('daily_sugar', 'sugar', 'Sugar', '% of calories'),
        ('daily_salt', 'salt', 'Salt', 'g')
    ]
    
    for profile_key, range_key, display_name, unit in nutrients_to_check:
        value = profile[profile_key]
        range_data = recommended_ranges[range_key]
        information.append(
            check_nutrient_level(
                value, 
                range_data['min'], 
                range_data['max'], 
                display_name,
                unit
            )
        )
    
    return information




