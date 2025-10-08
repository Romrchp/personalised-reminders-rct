import pandas as pd


def group_and_aggregate_nutrients(df):
    """
    Groups rows by 'consumed_at', concatenates strings, and sums numeric values.
    
    Parameters:
    df (DataFrame): The DataFrame to be grouped and aggregated.
    
    Returns:
    DataFrame: A new DataFrame with grouped and aggregated data.
    """
    concat_strings = lambda x: ' -- '.join(x)
    
    sum_ignore_nan = lambda x: x.sum(min_count=1)

    grouped_df = df.groupby('intake_id').agg({
        'food_name': concat_strings,
        'energy_kcal': 'sum',
        'water': 'sum',
        'protein': 'sum',
        'carbohydrates': 'sum',
        'fat': 'sum',
        'fatty_acids_saturated': sum_ignore_nan,
        'fiber': sum_ignore_nan,
        'sodium': sum_ignore_nan
    }).reset_index()
    
    return grouped_df


def group_by_date_and_aggregate_nutrients(df):
    """
    Groups rows by date, ignoring the time part of 'consumed_at', and sums numeric nutritional values.
    
    Parameters:
    df (DataFrame): The DataFrame to be grouped and aggregated.
    
    Returns:
    DataFrame: A new DataFrame with data grouped by date and aggregated nutritional values.
    """
    # Ensure 'consumed_at' is a datetime type
    if not pd.api.types.is_datetime64_any_dtype(df['consumed_at']):
        df['consumed_at'] = pd.to_datetime(df['consumed_at'])

    # Extract date from 'consumed_at'
    df['date'] = df['consumed_at'].dt.date

    # Group by 'date', summing up nutritional values
    grouped_df = df.groupby('date').agg({
        'energy_kcal': 'sum',
        'water': 'sum',
        'protein': 'sum',
        'carbohydrates': 'sum',
        'fat': 'sum',
        'fatty_acids_saturated': 'sum',
        'fiber': 'sum'
    }).reset_index()

    return grouped_df


def group_by_intakeid(df, columns_to_sum=None, columns_to_min=None, columns_to_join=None, dict_columns=None):
    """
    Group data by intake_id, aggregating columns based on their types.
    
    Parameters:
    df (DataFrame): The DataFrame to be aggregated.
    columns_to_sum (list): Columns to aggregate by summing.
    columns_to_min (list): Columns to aggregate by taking the minimum value.
    columns_to_join (list): Columns to aggregate by joining strings.
    dict_columns (dict): Dictionary columns to merge, where keys are output column names and values are tuples of (key_col, value_col).
    
    Returns:
    DataFrame: A new DataFrame with rows aggregated by intake_id.
    """
    df = df.copy()
    df['consumed_at'] = pd.to_datetime(df['consumed_at'])
    df['local_time'] = pd.to_datetime(df['local_time'])
    
    #Saving the og dictionnary columns + store the og column for later processing
    if dict_columns:
        dict_cols_data = {}
        for output_col in dict_columns.keys():
            if output_col in df.columns:
                dict_cols_data[output_col] = df[output_col].copy()
                df.drop(columns=[output_col], inplace=True)
    
    #Preparing the string columns
    for col in columns_to_join or []:
       if col in df.columns:
           df[col] = df[col].astype(str).fillna('')
    
    #Preparing aggregation dictionnaries
    agg_dict = {}
    
    for col in columns_to_sum or []:
        if col in df.columns:
            agg_dict[col] = 'sum'

    for col in columns_to_min or []:
        if col in df.columns:
            agg_dict[col] = 'min'

    for col in columns_to_join or []:
        if col in df.columns:
            agg_dict[col] = lambda x: ', '.join(x)

    #DataFrame aggregation by intake_id
    if agg_dict:
        aggregated_df = df.groupby('intake_id').agg(agg_dict).reset_index()
    else:
        aggregated_df = df[['intake_id']].drop_duplicates().reset_index(drop=True)
    
    #------------------------- HANDLING DICTIONNARY COLUMNS ----------------------------

    if dict_columns:
        #First, handle existing dictionary columns if we already have some
        for output_col, saved_data in dict_cols_data.items():
            #Create a mapping from intake_id to merged dictionaries
            merged_dicts = {}
            for idx, group in df.groupby('intake_id'):
                # Get all dictionaries for this group
                dicts = [saved_data.iloc[i] for i in group.index if isinstance(saved_data.iloc[i], dict)]
                # Merge the latter
                if dicts:
                    result = {}
                    for d in dicts:
                        result.update(d)
                    merged_dicts[idx] = result
            
            # Finally, add the merged dictionaries to the aggregated DataFrame
            aggregated_df[output_col] = aggregated_df['intake_id'].map(merged_dicts)
        
        # Then, handle columns that need to be converted to dictionaries
        for output_col, (key_col, value_col) in dict_columns.items():
            if output_col not in dict_cols_data and key_col in df.columns and value_col in df.columns:
                # Create dictionaries from key-value pairs for each intake_id
                result_dicts = {}
                for idx, group in df.groupby('intake_id'):
                    result = {}
                    for k, v in zip(group[key_col], group[value_col]):
                        if not pd.isna(k) and not pd.isna(v):
                            result[k] = v
                    if result:
                        result_dicts[idx] = result
                
                # Add the created dictionaries to the aggregated DataFrame
                aggregated_df[output_col] = aggregated_df['intake_id'].map(result_dicts)
    
    return aggregated_df
    


def tmp_aggregate_by_time_window(df, time_window='10min'):
    """
    Aggregate rows based on a time difference criterion in the 'consumed_at' column,
    grouping entries within a specified time window and summing numeric columns.
    
    Parameters:
    df (DataFrame): The DataFrame to be aggregated.
    time_window (str): The time window for grouping, formatted as a pandas-compatible offset string.
    
    Returns:
    DataFrame: A new DataFrame with rows aggregated by the time window.
    """
    #Ensure 'consumed_at' is a datetime column + sort
    df['consumed_at'] = pd.to_datetime(df['consumed_at'])
    df = df.sort_values('consumed_at').reset_index(drop=True)
    
    #Initializing groups
    group_id = 0
    groups = [group_id]
    
    #Iterate through the DataFrame to prepare group IDs for each group
    for i in range(1, len(df)):
        if (df.loc[i, 'consumed_at'] - df.loc[i - 1, 'consumed_at']) <= pd.Timedelta(time_window):
            groups.append(group_id)
        else:
            group_id += 1
            groups.append(group_id)
    
    # Assign group IDs
    df['time_group'] = groups
    
    # Aggregate grouped data
    aggregated_df = df.groupby('time_group').agg({
        'local_time': 'min',  # Keeps the earliest consumed_at time in the group
        'energy_kcal': 'sum',
        'water': 'sum',
        'protein': 'sum',
        'carbohydrates': 'sum',
        'fat': 'sum',
        'fatty_acids_saturated': 'sum',
        'fiber': 'sum',
        'food_name': lambda x: ', '.join(x),
        'time_gap': 'first'
        # Add other columns as needed, adjusting aggregation methods if necessary
    }).reset_index(drop=True)
    
    return aggregated_df


def aggregate_by_time_window(df, time_window='30min', columns_to_sum=None, columns_to_min=None, columns_to_join=None, dict_columns=None):
    """
    Aggregate rows based on a time difference criterion in the 'consumed_at' column,
    grouping entries within a specified time window and aggregating columns based on their types.
    
    Parameters:
    df (DataFrame): The DataFrame to be aggregated.
    time_window (str): The time window for grouping, formatted as a pandas-compatible offset string.
    columns_to_sum (list): Columns to aggregate by summing.
    columns_to_min (list): Columns to aggregate by taking the minimum value.
    columns_to_join (list): Columns to aggregate by joining strings.
    dict_columns (dict): Dictionary columns to merge, where keys are output column names and values are tuples of (key_col, value_col).
    
    Returns:
    DataFrame: A new DataFrame with rows aggregated by the time window.
    """

    # Ensure 'consumed_at' is a datetime column
    df = df.copy()

    df['consumed_at'] = pd.to_datetime(df['consumed_at'])
    df = df.sort_values('consumed_at').reset_index(drop=True)

    #Preparing string columns
    for col in columns_to_join or []:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna('')
    
    #Sort, for chronological grouping
    df = df.sort_values('consumed_at').reset_index(drop=True)
    
    #Group by time window
    group_id = 0
    groups = [group_id]
    
    for i in range(1, len(df)):
        if (df.loc[i, 'consumed_at'] - df.loc[i - 1, 'consumed_at']) <= pd.Timedelta(time_window):
            groups.append(group_id)
        else:
            group_id += 1
            groups.append(group_id)
    
    df['time_group'] = groups

    # Pre-process dictionary columns before aggregation
    if dict_columns:
        # Save original dictionary columns, we handle them separetely to make sure everything works
        dict_cols_data = {}
        for output_col in dict_columns.keys():
            if output_col in df.columns:
                # Store the original column for later processing
                dict_cols_data[output_col] = df[output_col].copy()
                df.drop(columns=[output_col], inplace=True)
            
    # Prepare aggregation dictionary
    agg_dict = {}

    for col in columns_to_sum or []:
        if col in df.columns:
            agg_dict[col] = 'sum'

    for col in columns_to_min or []:
        if col in df.columns:
            agg_dict[col] = 'min'

    for col in columns_to_join or []:
        if col in df.columns:
            agg_dict[col] = lambda x: ', '.join(x)

    # Aggregate by time_group
    if agg_dict:
        aggregated_df = df.groupby('time_group').agg(agg_dict).reset_index()
    else:
        aggregated_df = df[['time_group']].drop_duplicates().reset_index(drop=True)
    

     #------------------------- HANDLING DICTIONNARY COLUMNS ----------------------------

    # Handle dictionary columns after aggregation
    if dict_columns:
        # First, handle existing dictionary columns
        for output_col, saved_data in dict_cols_data.items():
            # Create a mapping from time_group to merged dictionaries
            merged_dicts = {}
            for idx, group in df.groupby('time_group'):
                # Get all dictionaries for this group
                dicts = [saved_data.iloc[i] for i in group.index if isinstance(saved_data.iloc[i], dict)]
                # Merge dictionaries
                if dicts:
                    result = {}
                    for d in dicts:
                        result.update(d)
                    merged_dicts[idx] = result
            
            # Add the merged dictionaries to the aggregated DataFrame
            aggregated_df[output_col] = aggregated_df['time_group'].map(merged_dicts)
        
        # Then, handle columns that need to be converted to dictionaries
        for output_col, (key_col, value_col) in dict_columns.items():
            if output_col not in dict_cols_data and key_col in df.columns and value_col in df.columns:
                # Create dictionaries from key-value pairs for our time groups
                result_dicts = {}
                for idx, group in df.groupby('time_group'):
                    result = {}
                    for k, v in zip(group[key_col], group[value_col]):
                        if not pd.isna(k) and not pd.isna(v):
                            result[k] = v
                    if result:
                        result_dicts[idx] = result
                
                # Add the created dictionaries to the aggregated DataFrame
                aggregated_df[output_col] = aggregated_df['time_group'].map(result_dicts)
    
    return aggregated_df