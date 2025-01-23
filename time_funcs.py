import pandas as pd
import numpy as np
import requests

pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 150)


def return_current_gameweek(main_response):
    fixture_data = pd.json_normalize(main_response.json(), record_path='events')
    current_gameweek = fixture_data.is_current.ne(False).idxmax() + 1
    return current_gameweek


def most_recent_fixture():
    fixture_response = requests.get('https://fantasy.premierleague.com/api/fixtures/')
    fixture_data = pd.json_normalize(fixture_response.json())
    fixture_data = fixture_data[['event', 'finished', 'kickoff_time']]
    most_recent_fixture = fixture_data[fixture_data['finished'] == False].iloc[0].to_list()
    return most_recent_fixture


