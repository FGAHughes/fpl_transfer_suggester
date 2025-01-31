import requests
import pandas as pd


# Returns json file from FPL API that can be used to return element_master, fixture_master, etc
def return_main_response():
    main_response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
    return main_response


#
def return_element_fixtures(element_original_id):
    element_response = requests.get(f'https://fantasy.premierleague.com/api/element-summary/{element_original_id}/')
    element_fixtures = pd.json_normalize(element_response.json(), record_path='fixtures')
    return element_fixtures


def return_element_history(element_original_id):
    element_response = requests.get(f'https://fantasy.premierleague.com/api/element-summary/{element_original_id}/')
    element_history = pd.json_normalize(element_response.json(), record_path='history')
    return element_history


def return_element_master(main_response):
    element_master = pd.json_normalize(main_response.json(), record_path='elements')
    element_master = element_master[['id',
                                     'web_name',
                                     'team',
                                     'element_type',
                                     'chance_of_playing_next_round',
                                     'now_cost',
                                     'status']]
    element_master.insert(loc=1, column='og_id', value=element_master.id)
    element_master.reset_index(drop=True, inplace=True)
    element_master['id'] = element_master.index
    return element_master

