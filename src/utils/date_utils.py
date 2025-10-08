from datetime import datetime, timedelta

import pandas as pd


def convert_to_local_time(df):
    """
    Converts the 'consumed_at' column to datetime and then converts it to the 'Europe/Zurich' timezone.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing the 'consumed_at' column.

    Returns:
    - pd.DataFrame: The modified DataFrame with the 'local_time' column added.
    """
    if df is None:
        return None

    df['consumed_at'] = pd.to_datetime(df['consumed_at'])
    df['local_time'] = df['consumed_at'].dt.tz_convert('Europe/Zurich')

    return df


def get_last_week_dates():
    """
    Calculates the start and end dates of the previous week.

    Returns:
    tuple: A tuple containing the start and end dates of the previous week in 'YYYY-MM-DD' format.
    """

    current_date = datetime.now()

    current_week_start = current_date - timedelta(days=current_date.weekday())

    previous_week_start = current_week_start - timedelta(weeks=1)
    previous_week_end = previous_week_start + timedelta(days=6)

    previous_week_start = previous_week_start.strftime('%Y-%m-%d')
    previous_week_end = previous_week_end.strftime('%Y-%m-%d')
    
    return previous_week_start, previous_week_end


def get_last_month_dates():
    """
    Calculates the start and end dates of the last month.
    
    Returns:
    tuple: A tuple containing the start and end dates of the last month in 'YYYY-MM-DD' format.
    """
    current_date = datetime.now()

    first_day_current_month = current_date.replace(day=1)

    last_day_previous_month = first_day_current_month - timedelta(days=1)

    first_day_previous_month = last_day_previous_month.replace(day=1)

    first_day_previous_month = first_day_previous_month.strftime('%Y-%m-%d')
    last_day_previous_month = last_day_previous_month.strftime('%Y-%m-%d')
    
    return first_day_previous_month, last_day_previous_month