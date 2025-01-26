import requests
import pandas as pd
import time
import numpy as np

# show all columns
pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)

# from fetch_element_data import fetch_data_and_predict_points
from time_funcs import return_current_gameweek

# element_master, team_master, element_response = fetch_data_and_predict_points()


# current_gameweek = return_current_gameweek(element_response)


def return_manager_stats(manager_id, current_gameweek):
    gameweek_response = requests.get(f'https://fantasy.premierleague.com/api/entry/{manager_id}/event/{current_gameweek}/picks/')
    active_chip = gameweek_response.json()['active_chip']
    if active_chip == 'freehit':  # if free hit was active, then return elements from the gameweek prior
        gameweek_response = requests.get(f'https://fantasy.premierleague.com/api/entry/{manager_id}/event/{current_gameweek - 1}/picks/')
    else:
        pass
    gameweek_info = pd.json_normalize(gameweek_response.json(), record_path='picks')
    gameweek_elements = gameweek_info[['element']]
    gameweek_bank = pd.json_normalize(gameweek_response.json()).iloc[0, 10]
    return gameweek_elements, gameweek_bank


def suggest_transfers(my_elements, bank, element_master, gw_comparison):
    my_elements_data = my_elements.merge(element_master, how='left', left_on='element', right_on='og_id')
    element_master_copy = element_master.drop(element_master[element_master['minutes'] < 60].index)
    element_master_copy = element_master_copy.drop(element_master_copy[element_master_copy['chance_of_playing_next_round'] < 75].index)
    element_master_copy = element_master_copy.drop(element_master_copy[element_master_copy['starts'] < 2].index)
    relevant_element_info = element_master_copy[['web_name', 'element_type', f'pp_{gw_comparison}', 'now_cost']]
    suggested_transfers_main = pd.DataFrame(columns=['web_name', 'out', 'element_type'])
    for element in range(15):
        element_type = my_elements_data.element_type[element]
        element_pp = my_elements_data[f'pp_{gw_comparison}'][element]
        element_web_name = my_elements_data.web_name[element]
        element_cost = my_elements_data.now_cost[element]
        relevant_type_elements = relevant_element_info[relevant_element_info['element_type'] == element_type]
        relevant_type_elements = relevant_type_elements[~relevant_type_elements['web_name'].isin(my_elements_data['web_name'])]
        affordable_elements = relevant_type_elements[relevant_type_elements['now_cost'] <= element_cost+bank]
        suggested_transfers_sub = affordable_elements[affordable_elements[f'pp_{gw_comparison}'] > element_pp].head(3)
        if len(suggested_transfers_sub) > 0:
            suggested_transfers_sub.insert(column='out', loc=1, value=element_web_name)
            suggested_transfers_sub.insert(column='pp_difference', value=(relevant_type_elements[f'pp_{gw_comparison}']-element_pp), loc=len(suggested_transfers_sub))
            suggested_transfers_main = pd.concat([suggested_transfers_main, suggested_transfers_sub], ignore_index=True)
    suggested_transfers_main.rename(columns={'web_name': 'in'})
    suggested_transfers_main.sort_values(by='pp_difference', ascending=False, inplace=True)
    return suggested_transfers_main

def suggest_starting_xi(my_elements, element_master):
    my_elements_data = my_elements.merge(element_master, how='left', left_on='element', right_on='og_id')
    my_elements_data = my_elements_data.sort_values(by='pp_1', ascending=False, ignore_index=True)
    my_elements_data = my_elements_data[['web_name', 'pp_1', 'element_type']]
    starting_xi = pd.DataFrame(columns=['web_name', 'pp_1', 'element_type'])
    bench = pd.DataFrame(columns=['web_name', 'pp_1', 'element_type'])
    element_type_needed = np.array([1, 3, 2, 1])
    slots_remaining = 11
    for i in range(15):
        type_id = my_elements_data.element_type[i] - 1
        if type_id == 0 and element_type_needed[type_id] == 0:
            bench.loc[len(bench)] = my_elements_data.iloc[i, :]
        # If there are spare slots remaining
        elif slots_remaining > sum(element_type_needed):
            # Add player to starting xi
            starting_xi.loc[len(starting_xi)] = my_elements_data.iloc[i, :]
            # Reduce slots remaining by 1 if
            slots_remaining -=1
            # If we don't already have enough of an element type, reduce the amount needed by 1
            if element_type_needed[type_id] > 0:
                element_type_needed[type_id] -=1
        # If there aren't spare slots remaining
        elif slots_remaining == sum(element_type_needed):
            if element_type_needed[type_id] > 0:
                starting_xi.loc[len(starting_xi)] = my_elements_data.iloc[i, :]
                slots_remaining -= 1
                if element_type_needed[type_id] > 0:
                    element_type_needed[type_id] -= 1
            else:
                bench.loc[len(bench)] = my_elements_data.iloc[i, :]
        else:
            bench.loc[len(bench)] = my_elements_data.iloc[i, :]

    starting_xi = pd.concat([starting_xi, bench], ignore_index=True)
    starting_xi.rename(columns={'pp_1': 'gameweek_points'})
    return starting_xi
