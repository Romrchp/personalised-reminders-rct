from datetime import datetime, timedelta

import pandas as pd

from src.constants import COLUMNS_OF_INTEREST


def filter_last_meal(df):
    """
    Filters the DataFrame to return the last meal based on the 'consumed_at' column,
    considering only meals consumed within a time window of one hour.
    """
    df['consumed_at'] = pd.to_datetime(df['consumed_at']).dt.tz_convert('UTC')
    last_meal_time = df['consumed_at'].max()
    one_hour_before = last_meal_time - timedelta(days=10)
    return df[(df['consumed_at'] >= one_hour_before) & (df['consumed_at'] <= last_meal_time)]


def filter_meals_on_date(df, date):
    """
    Filters the DataFrame to return meals consumed on the specified date.
    """
    df['consumed_at'] = pd.to_datetime(df['consumed_at']).dt.tz_convert('UTC')
    return df[df['consumed_at'].dt.date == date]


def filter_this_week(df):
    """
    Filters the DataFrame to return meals consumed this week.
    """
    df['consumed_at'] = pd.to_datetime(df['consumed_at']).dt.tz_convert('UTC')
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())
    return df[(df['consumed_at'].dt.date >= start_of_week) & (df['consumed_at'].dt.date <= today)]


def filter_today(df):
    """
    Filters the DataFrame to return meals consumed today.
    """
    df['consumed_at'] = pd.to_datetime(df['consumed_at']).dt.tz_convert('UTC')
    today = datetime.utcnow().date()
    return df[df['consumed_at'].dt.date == today]


def filter_date(df):
    df['consumed_at'] = pd.to_datetime(df['consumed_at'])
    df = df.set_index('consumed_at')

    filtered_logs = df.loc['2023-12-13']

    filtered_logs.reset_index()
    return filtered_logs


def filter_meals_by_date(df, date):
    """
    Filters the logs by the given date and selects specific columns of interest.
    
    Parameters:
    df (DataFrame): The DataFrame to filter.
    date (str): The date to filter by in 'YYYY-MM-DD' format.
    
    Returns:
    DataFrame: A DataFrame with logs from the specified date containing only the columns of interest.
    """

    if not pd.api.types.is_datetime64_any_dtype(df['consumed_at']):
        df['consumed_at'] = pd.to_datetime(df['consumed_at'])

    # Set 'consumed_at' as the DataFrame's index if it's not already
    if df.index.name != 'consumed_at':
        df = df.set_index('consumed_at')

    filtered_logs = df.loc[date]

    filtered_logs = filtered_logs[COLUMNS_OF_INTEREST]
 
    return filtered_logs.reset_index()


def filter_meals_by_date_range(df, start_date, end_date, columns_of_interest = None):
    """
    Filters the logs for a range of dates and selects specific columns of interest.
    
    Parameters:
    df (DataFrame): The DataFrame to filter.
    start_date (str): The start date to filter by in 'YYYY-MM-DD' format.
    end_date (str): The end date to filter by in 'YYYY-MM-DD' format.
    columns_of_interest (list): List of strings representing the columns to be included in the output.
    
    Returns:
    DataFrame: A DataFrame with logs from the specified date range containing only the columns of interest.
    """

    if not pd.api.types.is_datetime64_any_dtype(df['consumed_at']):
        df['consumed_at'] = pd.to_datetime(df['consumed_at'])

    if df.index.name != 'consumed_at':
        df = df.set_index('consumed_at')

    df = df.sort_index()

    # Check for duplicates and handle if necessary, for example by aggregating
    # If duplicates should be aggregated, you would include aggregation logic here

    filtered_logs = df.loc[start_date:end_date]

    filtered_logs = filtered_logs[COLUMNS_OF_INTEREST]
    
    return filtered_logs.reset_index()
