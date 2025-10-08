import csv
import os
import pandas as pd

def get_users_adresses() :
    base_directory = os.path.abspath(os.path.dirname(__file__))
    project_directory = os.path.join(base_directory, '..', '..')
    data_directory = os.path.join(project_directory,'data')
    users_data_file = os.path.join(data_directory,'google_form_users_data.csv')

    users_complete_data = pd.read_csv(users_data_file, dtype={'Phone Number': str})

    users_complete_data = users_complete_data[['Phone Number', 'E-mail Address']]

    return users_complete_data