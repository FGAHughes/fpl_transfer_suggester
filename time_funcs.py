import os
import pickle
from datetime import datetime

import pandas as pd
import numpy as np
import requests
from dateutil.relativedelta import relativedelta

from fpl_2425.fpl_transfer_suggester.os_funcs import make_directory

pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 150)

# A function that returns the current gameweek in FPL
def return_current_gameweek(main_response):
    # Obtain gameweek data df from main_response
    gameweek_data = pd.json_normalize(main_response.json(), record_path='events')
    # Determine current gameweek by finding the last gameweek where finished == True and then returning the gameweek after
    current_gameweek = gameweek_data.is_current.ne(False).idxmax() + 1
    return current_gameweek


# A function that returns the last time the data was updated, returning None if the program was never ran before
def return_last_update_time():
    make_directory('last_update_time')
    filepath = os.path.join('last_update_time', 'last_update_time')
    if os.path.exists(filepath):
        with open(filepath, "rb") as file:
            return pickle.load(file)
    return None


# A function to save the last time the data was updated, as a pickle file
def save_update_time():
    filepath = os.path.join('last_update_time', 'last_update_time')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(filepath, 'wb') as file:
        pickle.dump(current_time, file)


# A function to return whether the program needs to update element date or not
def update_or_not():
    # Create a df of fixtures, date and time, and if each has finished
    fixture_response = requests.get('https://fantasy.premierleague.com/api/fixtures/')
    fixture_data = pd.json_normalize(fixture_response.json())
    fixture_tracker = fixture_data[['event',
                                    'finished',
                                    'kickoff_time']]
    fixture_tracker.dropna(axis=0, inplace=True)
    # Convert fixture data and time to datetime
    fixture_tracker['kickoff_time'] = pd.to_datetime(fixture_tracker['kickoff_time'], format='%Y-%m-%dT%H:%M:%SZ')

    # Return the last time data was update, returning None if it has never been
    last_update_time = return_last_update_time()
    if last_update_time is None:
        return True
    # Save last update time
    last_update_time = datetime.strptime(last_update_time, '%Y-%m-%d %H:%M:%S')
    # Return the most recent fixture to have finished
    most_recent_fixture = fixture_tracker[fixture_tracker['finished'] == True].iloc[-1][2]  # to_list removed from here
    # Return update decision of True after every finished fixture or if data hasn't been updated every 12 hours (to
    # account for potential injuries and transfers)
    if (most_recent_fixture > last_update_time) or last_update_time < (datetime.now() - relativedelta(hours=12)):
        return True
    # Return False if not
    return False
