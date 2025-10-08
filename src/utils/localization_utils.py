# src/utils/localization_utils.py

import random
import os
import json

from flask import current_app


def get_localized_string(key, language):
    if language is None:
        language = 'en'
    localizations = current_app.extensions.get('localizations', {})

    localized_string = localizations.get(language, {}).get(key, key)
    return localized_string


def get_localized_random_string(key, language, app) -> str:
    if language is None:
        language = 'en'

    with app.app_context():
        localizations = current_app.extensions.get('localizations', {})
        string_list = localizations.get(language, {}).get(key)
        return random.choice(string_list)
    
def get_localized_meal_type(meal_type, language, app) -> str:

    with app.app_context():
        #We retrieve the meal types from our json file
        localized_meal_types = current_app.extensions.get('localizations', {}).get(language, {}).get('meal_types', {})
        
        #Return the localized meal type. Default is english if nothing is found.
        return localized_meal_types.get(meal_type, meal_type)
    


def get_localized_summary_element(key_path, language) -> str:
    """
    Retrieve a nested localized string from the JSON file using a dotted key path.
    Example: 'panel_b.panel-title' will return the title of panel B.
    """

    base_dir = os.path.dirname(__file__)  
    localization_file = os.path.join(base_dir, "..", "locales", f"{language}.json")

    # Load the file
    try:
        with open(localization_file, "r", encoding="utf-8") as f:
            localizations = json.load(f)
    except FileNotFoundError:
        return f"[Missing localization file: {language}.json]"

    # Traverse the key path
    keys = key_path.split(".")
    value = localizations
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return f"N/A"
        
    return value

def get_hei_translations(language):
    """
    Get HEI translations using your existing localization system
    """
    base_dir = os.path.dirname(__file__)  
    localization_file = os.path.join(base_dir, "..", "locales", f"{language}.json")
    
    try:
        with open(localization_file, "r", encoding="utf-8") as f:
            localizations = json.load(f)
        return localizations
    except FileNotFoundError:
        # Fallback to English if language file not found
        return {}


def get_language_code(language_name):
    if language_name.lower() == 'english':
        return 'en'
    elif language_name.lower() == 'french':
        return 'fr'
    elif language_name.lower() == 'german':
        return 'de'
    elif language_name.lower() == 'italian':
        return 'it'
    else:
        return 'en'

def prompt_language_formatting(language_code):
    if language_code == 'en' :
        return "English"
    elif language_code == 'fr' :
        return "French"
    elif language_code == 'de' :
        return "German"
    elif language_code == 'it' :
        return "Italian"
    else :
        return "English"