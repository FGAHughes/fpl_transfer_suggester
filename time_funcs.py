import pandas as pd
import numpy as np
import requests

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

# I feel like I must have used this but apparently I haven't. It's wrong anyway it should be the last fixture for
# Finished to equal True but I am just going to leave this hear, just in case...
# def most_recent_fixture():
#     # Obtain fixture data as df
#     fixture_response = requests.get('https://fantasy.premierleague.com/api/fixtures/')
#     fixture_data = pd.json_normalize(fixture_response.json())
#     # Select only columns with data we want to return
#     fixture_data = fixture_data[['event', 'finished', 'kickoff_time']]
#     # Locate most recent fixture by finding the last fixture where
#     most_recent_fixture = fixture_data[fixture_data['finished'] == False].iloc[0].to_list()
#     return most_recent_fixture


