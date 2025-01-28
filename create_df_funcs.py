import pandas as pd
import requests
from datetime import datetime
import numpy as np
import pickle
import os
from dateutil.relativedelta import relativedelta

from indv_stat_funcs import return_next_seven_opponents, past_x_performances
from os_funcs import make_directory

# show all columns
pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)


def return_main_response():
    main_response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
    return main_response


# a function to fetch and return element (player) data
def create_element_master(main_response, current_gameweek):
    print('element_master is under construction...')
    # Connect fpl API and fetch relevant dataframe
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

    all_element_stats = []
    all_element_fixtures = []
    previous_element_team = None
    elements_added = []
    for element in range(len(element_master)):
        element_og_id = element_master.og_id[element]
        element_team = element_master.team[element]
        element_fixtures_df, element_stats_df = create_element_dfs(element_og_id)
        # Ensures df isn't empty, which can happen if a new player has just been signed
        if element_stats_df.empty:
            element_stats = [0, 0, 0, 0, 0, 0, 0]
        else:
            element_stats = past_x_performances(element_stats_df, 9)
        if element_team != previous_element_team:
            element_fixtures = return_next_seven_opponents(element_team, element_fixtures_df, current_gameweek)
        else:
            pass
        all_element_stats.append(element_stats)
        all_element_fixtures.append(element_fixtures)
        previous_element_team = element_team
        if ((element % 100) == 0) and element != 0:
            print(f'The data of {element} elements has been added.')
        if element_master.id[element] in elements_added:
            print('Duplicate: ', element_master.id[element])
        elements_added.append(element_master.id[element])
    all_element_stats = np.asarray(all_element_stats, dtype='object')
    all_element_fixtures = np.asarray(all_element_fixtures, dtype='object')
    element_master[['xg_value', 'xa_value', 'xgc_value', 'saves', 'minutes', 'starts', 'bonus']] = all_element_stats
    element_master[['fix1a', 'fix1b',
                    'fix2a', 'fix2b',
                    'fix3a', 'fix3b',
                    'fix4a', 'fix4b',
                    'fix5a', 'fix5b',
                    'fix6a', 'fix6b',
                    'fix7a', 'fix7b'
                    ]] = all_element_fixtures
    element_master = add_positional_multipliers(element_master)
    element_master['chance_of_playing_next_round'] = element_master['chance_of_playing_next_round'].fillna(100.0)

    element_master = element_master.fillna(0)
    print('\"element_master\" created')
    return element_master


def add_positional_multipliers(element_master):
    positional_multipliers = pd.DataFrame({'element_type': [1, 2, 3, 4],
                                           'goal_multi': [6, 6, 5, 4],
                                           'assist_multi': [3, 3, 3, 3],
                                           'cs_multi': [4, 4, 1, 0]})
    updated_element_master = pd.merge(element_master, positional_multipliers, on='element_type')
    return updated_element_master


def add_team_data(team_master, element_master):
    element_master = element_master.merge(team_master, how='left', left_on='team', right_on='team_id')
    element_master.drop(columns='team_id', inplace=True)
    element_master = element_master.rename(columns={'team_xg': 'element_team_xg',
                                                    'team_xa': 'element_team_xa',
                                                    'team_xgc': 'element_team_xgc',
                                                    'team_name': 'element_team_name'
                                                    })
    return element_master


def predict_points(team_master, element_master, gw_comparison):
    # non_starters = element_master[element_master['starts'] == 0]
    # element_master = element_master.drop(element_master[element_master['starts'] == 0].index)
    for fixture in range(1, 8):
        element_master = predict_gameweek_points(element_master, team_master, fixture, 'a')
        element_master = predict_gameweek_points(element_master, team_master, fixture, 'b')

    for gw in range(1, 8):
        element_master = add_gw_predicted_points_column(element_master, gw)

    for gw in range(1, 8):
        element_master = add_cumulative_predict_points_column(element_master, gw)
    element_master = element_master[['id',
                                     'og_id',
                                     'web_name',
                                     'team',
                                     'element_type',
                                     'starts',
                                     'minutes',
                                     'now_cost',
                                     'bonus',
                                     'xg_value',
                                     'xa_value',
                                     'xgc_value',
                                     'chance_of_playing_next_round',
                                     'gw1_pp',
                                     'gw2_pp',
                                     'gw3_pp',
                                     'gw4_pp',
                                     'gw5_pp',
                                     'gw6_pp',
                                     'gw7_pp',
                                     'pp_1',
                                     'pp_2',
                                     'pp_3',
                                     'pp_4',
                                     'pp_5',
                                     'pp_6',
                                     'pp_7'
                                     ]]
    element_master[['minutes',
                    'now_cost',
                    'bonus',
                    'xg_value',
                    'xa_value',
                    'xgc_value',
                    'chance_of_playing_next_round',
                    'gw1_pp',
                    'gw2_pp',
                    'gw3_pp',
                    'gw4_pp',
                    'gw5_pp',
                    'gw6_pp',
                    'gw7_pp',
                    'pp_1',
                    'pp_2',
                    'pp_3',
                    'pp_4',
                    'pp_5',
                    'pp_6',
                    'pp_7']] = \
        element_master[['minutes',
                        'now_cost',
                        'bonus',
                        'xg_value',
                        'xa_value',
                        'xgc_value',
                        'chance_of_playing_next_round',
                        'gw1_pp',
                        'gw2_pp',
                        'gw3_pp',
                        'gw4_pp',
                        'gw5_pp',
                        'gw6_pp',
                        'gw7_pp',
                        'pp_1',
                        'pp_2',
                        'pp_3',
                        'pp_4',
                        'pp_5',
                        'pp_6',
                        'pp_7']].round(decimals=2)
    element_master.sort_values(by=f'pp_{gw_comparison}', ascending=False, inplace=True)
    element_master.to_csv('element_master.csv', index=False)
    return element_master


def create_team_master(element_master):
    team_df = []
    # Appending team '0' which will be used for blank gameweeks
    team_df.append([0, 'BLANK', 0, 0, 0])
    team_names = ['ARS', 'AVL', 'BOU', 'BRE', 'BRI', 'CHE', 'CRY', 'EVE', 'FUL', 'IPS',
                  'LEI', 'LIV', 'MCI', 'MUN', 'NEW', 'NFO', 'SOU', 'TOT', 'WHU', 'WOL']
    for i in range(1, 21):
        team_row = []
        team_players = element_master.groupby('team').get_group(i)
        team_row.append(i)
        team_row.append(team_names[i - 1])
        team_row.append((sum(team_players.xg_value)))
        team_row.append((sum(team_players.xa_value)))
        team_row.append(sum(team_players.xgc_value) / 11)
        team_df.append(team_row)
    team_master = pd.DataFrame(team_df, columns=['team_id',
                                                 'team_name',
                                                 'team_xg',
                                                 'team_xa',
                                                 'team_xgc'
                                                 ])
    print('\"team_master\" created')
    return team_master


# A function that returns an elements upcoming fixtures and stats in previous fixtures
def create_element_dfs(element_original_id):
    element_response = requests.get(f'https://fantasy.premierleague.com/api/element-summary/{element_original_id}/')
    element_fixtures = pd.json_normalize(element_response.json(), record_path='fixtures')
    element_history = pd.json_normalize(element_response.json(), record_path='history')
    return element_fixtures, element_history


def update_or_not():
    fixture_response = requests.get('https://fantasy.premierleague.com/api/fixtures/')
    fixture_data = pd.json_normalize(fixture_response.json())
    fixture_tracker = fixture_data[['event',
                                    'finished',
                                    'kickoff_time']]
    fixture_tracker.dropna(axis=0, inplace=True)
    fixture_tracker['kickoff_time'] = pd.to_datetime(fixture_tracker['kickoff_time'], format='%Y-%m-%dT%H:%M:%SZ')

    last_update_time = return_last_update_time()
    if last_update_time == None:
        return True
    last_update_time = datetime.strptime(last_update_time, '%Y-%m-%d %H:%M:%S')
    most_recent_fixture = fixture_tracker[fixture_tracker['finished'] == True].iloc[-1].to_list()[2]
    # updates after every fixture or at least 12 hours since it was last updated
    if (most_recent_fixture > last_update_time) or last_update_time < (datetime.now() - relativedelta(hours=12)):
        return True
    return False


def save_update_time():
    filepath = os.path.join('last_update_time', 'last_update_time')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(filepath, 'wb') as file:
        pickle.dump(current_time, file)


def return_last_update_time():
    make_directory('last_update_time')
    filepath = os.path.join('last_update_time', 'last_update_time')
    if os.path.exists(filepath):
        with open(filepath, "rb") as file:
            return pickle.load(file)
    return None


def add_gw_predicted_points_column(element_master, gw):
    element_master[f'gw{gw}_pp'] = element_master[f'gw{gw}_ppa'] + element_master[f'gw{gw}_ppb']
    return element_master


def add_cumulative_predict_points_column(element_master, forecast_gameweeks):
    element_master[f'pp_{forecast_gameweeks}'] = 0
    for gw in range(1, forecast_gameweeks + 1):
        element_master[f'pp_{forecast_gameweeks}'] += element_master[f'gw{gw}_ppa'] + element_master[
            f'gw{gw}_ppb']

    return element_master


def predict_gameweek_points(element_master, team_master, gameweek, a_or_b):
    upcomming_fixture = f'fix{gameweek}{a_or_b}'
    element_master = element_master.merge(team_master, how='left', left_on=upcomming_fixture, right_on='team_id')
    expected_goal_points = ((element_master.xg_value / element_master.element_team_xg
                             * (
                                     element_master.team_xgc + element_master.element_team_xg) / 2)) * element_master.goal_multi
    expected_assist_points = ((element_master.xa_value / element_master.element_team_xg)
                              * ((
                                         element_master.team_xgc + element_master.element_team_xg) / 2)) * element_master.assist_multi
    expected_cs_points = 2.718281828459045 ** (
        -((element_master.element_team_xgc + element_master.team_xg) / 2)) * element_master.cs_multi
    expected_save_points = element_master.saves / 3
    expected_bonus = element_master.bonus
    element_master[f'gw{gameweek}_pp{a_or_b}'] = (expected_goal_points +
                                                  expected_assist_points +
                                                  expected_save_points +
                                                  expected_cs_points +
                                                  expected_bonus)
    element_master[f'gw{gameweek}_pp{a_or_b}'] = element_master.apply(
        lambda row: row[f'gw{gameweek}_pp{a_or_b}'] + 2 if row['minutes'] > 60 else row[f'gw{gameweek}_pp{a_or_b}'] + 1
        if 0 < row['minutes'] < 60 else row[f'gw{gameweek}_pp{a_or_b}'], axis=1)
    element_master[f'gw{gameweek}_pp{a_or_b}'] = element_master.apply(
        lambda row: 0 if (row['chance_of_playing_next_round'] < 75 or row['starts'] <= 2) else row[
            f'gw{gameweek}_pp{a_or_b}'], axis=1)
    element_master[f'gw{gameweek}_pp{a_or_b}'] = element_master.apply(
        lambda row: 0 if row[f'fix{gameweek}{a_or_b}'] == 0 else row[f'gw{gameweek}_pp{a_or_b}'], axis=1)
    element_master.drop(columns=['team_xg', 'team_xa', 'team_xgc', 'team_id', 'team_name'], inplace=True)
    return (element_master)
