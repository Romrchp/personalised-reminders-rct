import os

import numpy as np
import pandas as pd
import csv
import shutil
from tempfile import NamedTemporaryFile

from src.config.logging_config import Logger
from src.constants import (GOOGLE_FORM_CSV_FILENAME, MFR_COHORT_ID_KEY,
                           MFR_ENV_KEY, UPDATE_GOOGLE_FORM_CSV_FILENAME)
from src.data_manager.models import User
from src.data_manager.user import is_user_registered
from src.db_session import session_scope
from src.utils.csv_utils import read_csv_to_dataframe
from src.utils.localization_utils import get_language_code

from .myfoodrepo_api_handler import create_myfoodrepo_service_instance

#Getting the logger for the 'form_data_manager'.
logger = Logger('myfoodrepo.data_manager.form_data_manager').get_logger()


def get_participation_keys():
    """
    Retrieves participation keys for a specific cohort within MyFoodRepo.
    
    Returns:
        list: A list of participation keys retrieved from MFR.
    
    """

    #Fetching MFR API key & cohort ID from the .env.
    mfr_key = os.environ.get(MFR_ENV_KEY)
    cohort_id = os.environ.get(MFR_COHORT_ID_KEY)

    #If all good -> initializes a MFR service instance & iterates through participants to return the keys
    if mfr_key is not None and cohort_id is not None:
        try:
            myfoodrepo_service = create_myfoodrepo_service_instance(mfr_key, cohort_id)

            participation_keys = []
            participations_page = 1
            while participations_page:
                participations, participations_page, included = myfoodrepo_service.list_cohort_participations(cohort_id)
                participation_keys += [item['attributes']['key'] for item in participations]

            print(f"The Keys are: {participation_keys}")
            return participation_keys
        except Exception as e:
            logger.error(f"Error generating participation keys: {e}")
            return []


def generate_participation_keys(quantity):

    """
    Generates a specified number of participation keys for a cohort in MyFoodRepo.
    
    Args:
        quantity (int): The number of participation keys to generate.

    Returns:
        str or None: ?????
    """
    mfr_key = os.environ.get(MFR_ENV_KEY)
    cohort_id = os.environ.get(MFR_COHORT_ID_KEY)

    if mfr_key is not None and cohort_id is not None:
        try:
            myfoodrepo_service = create_myfoodrepo_service_instance(mfr_key, cohort_id)

            participation_keys = []
            for _ in range(quantity):
                participation = myfoodrepo_service.create_cohort_participation(cohort_id)
                participation_key = participation["attributes"]["key"]
                participation_keys.append(participation_key)

            logger.info(f"Generated: {len(participation_keys)} participation keys")
            return participation_key
        except Exception as e:
            logger.error(f"Error generating participation keys: {e}")
            return        

def generate_participation_key():
    """
    Generates a single participation key for a cohort in MyFoodRepo.

    Returns:
        str or None: The generated participation key, or `None` if an error occurs.

    """

    mfr_key = os.environ.get(MFR_ENV_KEY)
    cohort_id = os.environ.get(MFR_COHORT_ID_KEY)

    if mfr_key is not None and cohort_id is not None:
        try:
            myfoodrepo_service = create_myfoodrepo_service_instance(mfr_key, cohort_id)

            participation = myfoodrepo_service.create_cohort_participation(cohort_id)
            participation_key = participation["attributes"]["key"]
            #participation_id = participation["id"]
            #updated_participation = myfoodrepo_service.update_participation_end_time(participation_id)
            print(participation["attributes"])

            logger.info(f"✅ Participation Key: {participation_key} succesfully generated")
            return participation_key
        except Exception as e:
            logger.error(f"🛑 Error generating participation keys: {e}")
            return



def update_cohort_participants_info():
    base_directory = os.path.abspath(os.path.dirname(__file__))
    project_directory = os.path.join(base_directory, '..', '..')
    data_directory = os.path.join(project_directory, 'data')

    current_cohort_csv_path = os.path.join(data_directory, GOOGLE_FORM_CSV_FILENAME)
    new_csv_file_path = os.path.join(data_directory, UPDATE_GOOGLE_FORM_CSV_FILENAME)

    try:
        # Load existing data
        with open(current_cohort_csv_path, mode='r', newline='', encoding='utf-8') as current_file:
            reader = csv.DictReader(current_file)
            fieldnames = reader.fieldnames
            existing_rows = list(reader)

        # Load new data
        with open(new_csv_file_path, mode='r', newline='', encoding='utf-8') as new_file:
            new_reader = csv.DictReader(new_file)
            if new_reader.fieldnames != fieldnames:
                raise ValueError("CSV format mismatch between existing and update files.")
            new_rows = list(new_reader)

        existing_set = {tuple(row.items()) for row in existing_rows}
        new_unique_rows = [row for row in new_rows if tuple(row.items()) not in existing_set]

        if not new_unique_rows:
            logger.debug("No new unique rows to add for the cohort CSV.")
            return

        with NamedTemporaryFile(mode='w', newline='', delete=False, encoding='utf-8') as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_rows)
            writer.writerows(new_unique_rows)
            temp_file_path = temp_file.name

        shutil.move(temp_file_path, current_cohort_csv_path)
        logger.debug(f"Updated cohort CSV with {len(new_unique_rows)} new entries.")

    except Exception as e:
        logger.error(f"Cohort participants update failed: {e}")


def fill_db_from_google_form_data():

    """
    Populates the database with user data, extracted from a GForm CSV file.
    
    Returns:
        tuple: A message string and an associated HTTP status code, differing on success or failure.
    
    """
    try:
        #Starting the database session & resolving files paths
        with session_scope() as session:
            base_directory = os.path.abspath(os.path.dirname(__file__))
            project_directory = os.path.join(base_directory, '..', '..')
            data_directory = os.path.join(project_directory, 'data')

            csv_file_path = os.path.join(data_directory, GOOGLE_FORM_CSV_FILENAME)

            #Loading the CSV file to populate 
            try:  #TODO: change this thing
                df = pd.read_csv(csv_file_path)
            except FileNotFoundError:
                logger.error(f"CSV file not found at {csv_file_path}")
                return "Error while processing Google Form Data", 500
            except Exception as e:
                logger.error(f"An error occurred while reading the CSV file: {e}")
                return "Error while processing Google Form Data", 500

            df['study_group'] = np.random.randint(0, 4, size=len(df))

            #Iterating through the dataframe and creating new user record if needed
            for index, row in df.iterrows():
                try:
                    phone_number = "+" + str(row['Phone Number'])
                    if is_user_registered(phone_number):
                        continue
                    
                    raw_gender = str(row.get('Gender', '')).strip().lower()
                    if raw_gender == 'male':
                        gender = 'M'
                    elif raw_gender == 'female':
                        gender = 'F'
                    elif raw_gender == 'non-binary':
                        gender = 'NB'
                    elif raw_gender == 'prefer not to say':
                        gender = 'NA'
                    else:
                        gender = 'NA'

                    myfoodrepo_key = generate_participation_key()
                    user = User(
                        phone_number=phone_number,
                        myfoodrepo_key=myfoodrepo_key,
                        gender=gender,
                        age=row.get('Age'),
                        language=get_language_code(row.get('Preferred Language')),
                        diet_goal=row.get('Dietary Goal'),
                        study_group=int(row['study_group'])
                    )
                    #Adding the user
                    session.add(user)
                except Exception as e:
                    logger.error(f"Failed to process row {index}: {e}")
                    continue

            logger.info("Database has been populated with users Google Form data")
            return "Google Form Data processed correctly", 200
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return "Error while processing Google Form Data", 500
