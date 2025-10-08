"""
Description: Facilitates data exchange with the MyFoodRepo script to retrieve necessary user data
(e.g., meal logs, patterns of forgetfulness) or to post updates.
Responsibility: Ensures that the agent has access to the latest user data and that any new data
 generated during interactions is correctly updated in the system.
"""
import os
import shutil
import pandas as pd

from src.data_manager.meal import get_most_recent_meal_time, get_recent_meals_string_for_user
from export_cohort_data import (ExportCohortAnnotationsService,
                                MyFoodRepoService)
from src.config.logging_config import Logger
from src.constants import (COHORT_ANNOTATIONS_CSV_FILENAME, DATA_FOLDER_NAME,
                           MFR_COHORT_ID_KEY, MFR_ENV_KEY,DB_UPDATE_DAYS_WINDOW)
from src.db_session import session_scope
from src.services.meal_grouping import (aggregate_by_time_window,
                                        group_by_intakeid)
from src.utils.csv_utils import read_csv_to_dataframe
from src.utils.date_utils import convert_to_local_time
from src.utils.pandas_utils import delete_empty_rows, get_json_from_df_row

from .models import Meal, User

logger = Logger('myfoodrepo.data_manager.myfoodrepo_data_manager').get_logger()

def insert_user_meal_data_to_db(df, participation_key):
    """
    Inserts meal data for a user into the database.
    
    Processes a DataFrame containing meal data and inserts new meal records 
    into the database for a user identified by their participation key. If a meal with the 
    same datetime already exists for the user, its description is updated instead of inserting a duplicate.
    
    Args: 
        df (pd.DataFrame): The database `DataFrame`.
        participation_key (str): The MyFoodRepo participation key.

    Returns:
        None.
    """
    with session_scope() as session:
        try:
            user = session.query(User).filter(User.myfoodrepo_key == participation_key).first()
            if user is None:
                logger.warning(f"No user found for participation_key: {participation_key}")
                return

            meals_added_count = 0
            for _, row in df.iterrows():
                meal_description = row['food_name']
                meal_datetime = row['local_time']
                food_ids = row['food_ids']
                eaten_quantities = row['eaten_quantities']

                existing_meal = session.query(Meal).filter_by(
                    user_id=user.id, datetime=meal_datetime,
                ).first()

                if existing_meal is not None:
                    if existing_meal.description != meal_description:
                        logger.info(f"Updating meal description for user {user.id} at {meal_datetime}")
                        existing_meal.description = meal_description

                    if existing_meal.nutrients != get_json_from_df_row(row):
                        logger.info(f"Updating meal nutrients for user {user.id} at {meal_datetime}")
                        existing_meal.nutrients = get_json_from_df_row(row)

                    if existing_meal.eaten_quantities != eaten_quantities :
                        logger.info(f"Updating meal eaten quantities for user {user.id} at {meal_datetime}")
                        existing_meal.eaten_quantities = eaten_quantities
                    
                    if existing_meal.food_ids != food_ids :
                        logger.info(f"Updating meal food ids for user {user.id} at {meal_datetime}")
                        existing_meal.food_ids = food_ids
                    continue  

                meal = Meal(
                    user_id=user.id,
                    description=meal_description,
                    nutrients=get_json_from_df_row(row),
                    food_ids = food_ids,
                    datetime=meal_datetime,
                    eaten_quantities = eaten_quantities
                )

                logger.debug(f"Adding meal: {meal.description} for user {user.id} at {meal.datetime}")
                session.add(meal)
                meals_added_count += 1

            if meals_added_count > 0:
                logger.info(f"{meals_added_count} newly logged meals have been inserted into the db for user: {user.id}")
            else:
                logger.info(f"No newly logged meals found for user {user.id}")

            most_recent_datetime = get_most_recent_meal_time(get_recent_meals_string_for_user(participation_key))
            logger.info(f"The most recent log meal for user {user.id} is {str(most_recent_datetime)}")
            user.last_meal_log = most_recent_datetime
            session.add(user)

        except Exception as e:
            logger.error(f"Failed to add meal data: {e}")
            raise e
        

def healthy_index_preprocessing(user):
    """
    Processes a specific user's data from the cohort's annotation file, specifically for HEI calculation.

    Args:
        User : The user for which we aim to compute the HEI

    Returns:
        (DataFrame) :  A dataframe containing the user's food information, correctly formatted.
    
    """

    cohort_df = load_data_from_csv()
    cohort_df = convert_to_local_time(cohort_df)
    cohort_df = delete_empty_rows(cohort_df)
    
    user_df = cohort_df[cohort_df['participation_key'] == user.myfoodrepo_key]
    
    return user_df




def process_user_data(df, participation_key, start_date=None, end_date=None):   
    """
    Processes and inserts meal data for a specific user.
    For a specific user, groups the data by intakeID, aggregates the meals,
    and inserts it into the database.

    Optionally filters the data based on a specific date range.

    Args:
        df (pd.DataFrame): the database `DataFrame`.
        participation_key (str): The MyFoodRepo participation key of a specific user.
        start_date (str, optional): The start date to filter the data (inclusive).
        end_date (str, optional): The end date to filter the data (inclusive).
    
    Returns:
        None.
    """
    # Make a copy of the dataframe for this user
    user_data = df[df['participation_key'] == participation_key].copy()
    
    # Debug information
    #logger.debug(f"Processing data for user {participation_key}")
    #logger.debug(f"User data shape: {user_data.shape}")
    
    if start_date:
        user_data = user_data[user_data['consumed_at'] >= pd.to_datetime(start_date)]
    
    if end_date:
        user_data = user_data[user_data['consumed_at'] <= pd.to_datetime(end_date)]

    # Define the columns for which we want to retrieve the user's information.
    timestamp_columns = ['consumed_at','local_time']
    text_columns = ['food_name']
    value_columns = [
        'energy_kcal','fat','fatty_acids_saturated','carbohydrates','sugar','salt',
        'fiber','calcium','iron','zinc','phosphorus', 'fatty_acids_polyunsaturated',
        'fatty_acids_monounsaturated', 'alcohol','starch','sodium','water','protein',
        'cholesterol'
    ]
    
    food_ids = {
        'food_ids': ('food_name','food_id'),
        'eaten_quantities': ('food_name','consumed_quantity')
    }

    # Ensure food_id and food_name are strings before grouping
    user_data['food_id'] = user_data['food_id'].astype(str).fillna('')
    user_data['food_name'] = user_data['food_name'].astype(str).fillna('')
    
    # Debug check for non-empty food names in user data
    if user_data['food_name'].isna().any() or (user_data['food_name'] == '').any():
        logger.warning(f"Found {(user_data['food_name'].isna() | (user_data['food_name'] == '')).sum()} rows with empty food names")
    
    # Group by intake_id
    grouped_data = group_by_intakeid(
        user_data,
        columns_to_sum=value_columns,
        columns_to_min=timestamp_columns,
        columns_to_join=text_columns,
        dict_columns=food_ids
    )
    
    
    # Aggregate by time window
    aggregated_data = aggregate_by_time_window(
        grouped_data,
        columns_to_sum=value_columns,
        columns_to_min=timestamp_columns,
        columns_to_join=text_columns,
        dict_columns=food_ids
    )
    
    
    try:
        insert_user_meal_data_to_db(aggregated_data, participation_key)
    except Exception as e:
        logger.error(f"Error inserting meal data for user {participation_key}: {e}")
        # Log more detailed error info
        logger.error(f"Error details: {str(e)}")
        raise e


def move_product_to_food(df):
    """
    Moves product information to food columns when food information is missing.
    """
    df = df.copy()
    
    df['food_id'] = df.apply(
        lambda row: row['product_id'] if pd.isna(row['food_id']) or str(row['food_id']).strip() == '' 
                    else row['food_id'], 
        axis=1
    )
    
    df['food_name'] = df.apply(
        lambda row: row['product_name'] if pd.isna(row['food_name']) or str(row['food_name']).strip() == '' 
                    else row['food_name'], 
        axis=1
    )

    df['food_id'] = df['food_id'].astype(str).fillna('')
    df['food_name'] = df['food_name'].astype(str).fillna('')
    
    return df
    

def load_data_from_csv():

    """
    Loads cohort annotation data from a CSV file into a DataFrame.
    
    Returns:
        pandas.DataFrame: A DataFrame containing the data from the CSV file.
    
    """
    csv_file_path = os.path.join(DATA_FOLDER_NAME, COHORT_ANNOTATIONS_CSV_FILENAME)
    return read_csv_to_dataframe(csv_file_path)


def download_csv(full_sync = True):
    """
    Downloads the cohort annotation CSV File from MyFoodRepo, and updates the local dataset
    
    Behavior:
        Connects to the MyFoodRepo, requests the cohort annotations CSV file and
        then updates the local dataset. If a previous version of the CSV file exists,
        it is replaced with the newly downloaded one.

    Note:
        The function requires `MFR_ENV_KEY`, `MFR_COHORT_ID_KEY`, `MFR_UID`, `MFR_CLIENT` and
        `MFR_ACCESS_TOKEN` to be set in the environment variables.
    
    """
    arg1 = os.environ.get(MFR_ENV_KEY)
    arg2 = os.environ.get(MFR_COHORT_ID_KEY)

    if arg1 is not None and arg2 is not None:
        try:
            host_mapping = {
                "local": MyFoodRepoService.LOCAL_HOST,
                "staging": MyFoodRepoService.STAGING_HOST,
                "production": MyFoodRepoService.PRODUCTION_HOST
            }

            host = host_mapping.get(arg1)
            if not host:
                logger.error(f"Invalid environment specified: {arg1}. Cannot determine the correct host.")
                return
            
            base_directory = os.path.abspath(os.path.dirname(__file__))
            project_directory = os.path.join(base_directory, '..', '..')
            database_directory = os.path.join(project_directory, 'data')

            os.makedirs(database_directory,exist_ok=True)

            
            new_csv_path = os.path.join(project_directory, COHORT_ANNOTATIONS_CSV_FILENAME)
            existing_csv_path = os.path.join(database_directory, COHORT_ANNOTATIONS_CSV_FILENAME)

            if full_sync :
                myfoodrepo_service = MyFoodRepoService(host=host,
                                                   uid=os.getenv("MFR_UID"),
                                                   client=os.getenv("MFR_CLIENT"),
                                                   access_token=os.getenv("MFR_ACCESS_TOKEN"))
                export_service = ExportCohortAnnotationsService(myfoodrepo_service, arg2)
                export_service.call(csv_path=new_csv_path,existing_csv_path=existing_csv_path)
            elif not full_sync :
                myfoodrepo_service = MyFoodRepoService(host=host,
                                                   uid=os.getenv("MFR_UID"),
                                                   client=os.getenv("MFR_CLIENT"),
                                                   access_token=os.getenv("MFR_ACCESS_TOKEN"),
                                                   days_window=DB_UPDATE_DAYS_WINDOW)
                export_service = ExportCohortAnnotationsService(myfoodrepo_service, arg2)
                export_service.call(csv_path=new_csv_path,existing_csv_path=existing_csv_path)



            if os.path.exists(existing_csv_path):
                logger.info("The cohort annotation .csv file was succesfully downloaded!")
                shutil.copyfile(new_csv_path, existing_csv_path)
            else:
                logger.info("The cohort annotation .csv file was succesfully downloaded for the first time!")
                with open(existing_csv_path, 'w'):
                    shutil.copyfile(new_csv_path, existing_csv_path)
            os.remove(new_csv_path)
        except Exception as e:
            logger.error(f"Error running the Cohort Annotation Data script: {e}")
            return
    else:
        logger.error("One or both required environment variables for the MFR API are missing. Cannot Update.")


def update_database(full_sync=False):
    """
    Updates the database with meal data from the latest cohort annotations CSV file.
    
    It handles downloading, processing, and updating the data into the SQLite database, using
    the `download_csv`and `load_data_from_csv` functions (among others).
    """

    if full_sync == True :
        logger.info("Database Meals - Complete update process started...")
        download_csv()
    elif full_sync == False : 
        logger.info("Database Meals - Update process for the last 3 days started ...")
        download_csv(full_sync=False)
        
    
    df = load_data_from_csv()
    
    # Process the data
    df = convert_to_local_time(df)
    df = delete_empty_rows(df)
    
    
    df = move_product_to_food(df)
    
    # Add debug info
    #logger.debug(f"Dataframe after processing: {df.shape}")
    #logger.debug(f"Sample of food_id and food_name after processing: {df[['food_id', 'food_name']].head()}")
    
    if df is None or df.empty:
        logger.error("Failed to load data from CSV or dataframe is empty.")
        return

    participation_keys = df['participation_key'].unique()
    logger.info(f"Found {len(participation_keys)} unique participation keys")

    for key in participation_keys:
        process_user_data(df, key)
    logger.info("Database Meals update process finished.")

