import requests
import pandas as pd
import numpy as np

# show all columns
pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)


# A function to return the stats of the manager ID that was inputted into run_fpl_script function
def return_manager_stats(manager_id, current_gameweek):
    # Connect to fpl api and fetch manager's data for the current gameweek
    gameweek_response = requests.get(f'https://fantasy.premierleague.com/api/entry/{manager_id}/event/{current_gameweek}/picks/')
    # Check if a chip was in use
    active_chip = gameweek_response.json()['active_chip']
    # if free hit was active, return elements from the gameweek prior as it won't fetch the managers actual elements
    if active_chip == 'freehit':
        gameweek_response = requests.get(f'https://fantasy.premierleague.com/api/entry/{manager_id}/event/{current_gameweek - 1}/picks/')
    else:
        pass
    # Return manager info
    gameweek_info = pd.json_normalize(gameweek_response.json(), record_path='picks')
    # Return manager's elements
    gameweek_elements = gameweek_info[['element']][0:15]
    # Return the amount of money available in the manager's bank
    gameweek_bank = pd.json_normalize(gameweek_response.json()).iloc[0, 10]
    return gameweek_elements, gameweek_bank


# A function that returns the best transfers to make given a manager's team and the number of weeks they want to bring
# them in for
def suggest_transfers(my_elements, bank, element_master, gw_comparison):
    # Add element data to each of the manager's elements
    my_elements_data = my_elements.merge(element_master, how='left', left_on='element', right_on='og_id')
    # Make a copy of element_master, only with player's we may consider bringing in
    element_master_copy = element_master.drop(element_master[element_master['minutes'] < 60].index)
    element_master_copy = element_master_copy.drop(element_master_copy[element_master_copy['chance_of_playing_next_round'] < 75].index)
    element_master_copy = element_master_copy.drop(element_master_copy[element_master_copy['starts'] < 1].index)
    relevant_element_info = element_master_copy[['web_name', 'element_type', f'pp_{gw_comparison}', 'now_cost']]
    # Create a df that will be used to store suggested transfers
    suggested_transfers_main = pd.DataFrame(columns=['web_name', 'out', 'element_type'])
    # For each element in manager's team
    for element in range(15):
        # Store relevant traits of manager's element
        element_type = my_elements_data.element_type[element]  # Position
        element_pp = my_elements_data[f'pp_{gw_comparison}'][element]
        element_web_name = my_elements_data.web_name[element]
        element_cost = my_elements_data.now_cost[element]
        # Only compare with elements of the same type (position), that aren't already in their team and are affordable
        relevant_type_elements = relevant_element_info[relevant_element_info['element_type'] == element_type]
        relevant_type_elements = relevant_type_elements[~relevant_type_elements['web_name'].isin(my_elements_data['web_name'])]
        affordable_elements = relevant_type_elements[relevant_type_elements['now_cost'] <= element_cost+bank]
        # Add the top 3 of these to df will be compiled to created suggested transfers
        suggested_transfers_sub = affordable_elements[affordable_elements[f'pp_{gw_comparison}'] > element_pp].head(3)
        # If there were any suggested transfers for the element
        if len(suggested_transfers_sub) > 0:
            #  Add column of the manager's element to transfer out
            suggested_transfers_sub.insert(column='out', loc=1, value=element_web_name)
            # Calculate the predicted point difference and make a column
            suggested_transfers_sub.insert(column='pp_difference', value=(relevant_type_elements[f'pp_{gw_comparison}']-element_pp), loc=len(suggested_transfers_sub))
            # Add suggested transfers to main suggested transfer df
            suggested_transfers_main = pd.concat([suggested_transfers_main, suggested_transfers_sub], ignore_index=True)
    suggested_transfers_main.rename(columns={'web_name': 'in'})
    # Sort by the transfers that would result in the greatest difference in points
    suggested_transfers_main.sort_values(by='pp_difference', ascending=False, inplace=True)
    return suggested_transfers_main


# A function to suggest the best starting XI for the manager ID's team
def suggest_starting_xi(my_elements, element_master):
    # Add element data to each of the manager's elements
    my_elements_data = my_elements.merge(element_master, how='left', left_on='element', right_on='og_id')
    # Sort elements by predicted points in the next gameweek
    my_elements_data = my_elements_data.sort_values(by='pp_1', ascending=False, ignore_index=True)
    # Select only necessary columns
    my_elements_data = my_elements_data[['web_name', 'pp_1', 'element_type']]
    # Create dfs to store starting XI and bench
    starting_xi = pd.DataFrame(columns=['web_name', 'pp_1', 'element_type'])
    bench = pd.DataFrame(columns=['web_name', 'pp_1', 'element_type'])
    # An array to store the minimum number of each position the XI must contain
    element_type_needed = np.array([1, 3, 2, 1])
    # Used to count number of slots remaining of the XI
    slots_remaining = 11
    for i in range(15):
        type_id = my_elements_data.element_type[i] - 1  # element's position's index in 'element_type_needed'
        # If XI already has a gk, add the other to bench
        if type_id == 0 and element_type_needed[type_id] == 0:
            bench.loc[len(bench)] = my_elements_data.iloc[i, :]
        # If there are spare slots remaining for any position
        elif slots_remaining > sum(element_type_needed):
            # Add element to starting xi
            starting_xi.loc[len(starting_xi)] = my_elements_data.iloc[i, :]
            # Reduce slots remaining by 1 if
            slots_remaining -=1
            # If we don't already have enough of that element type, reduce the amount needed by 1
            if element_type_needed[type_id] > 0:
                element_type_needed[type_id] -=1
        # If there are only slots remaining for certain positions
        elif slots_remaining == sum(element_type_needed):
            # If there is a slot remaining for this element's position
            if element_type_needed[type_id] > 0:
                # Add them to XI
                starting_xi.loc[len(starting_xi)] = my_elements_data.iloc[i, :]
                slots_remaining -= 1
                # If we don't already have enough of that element type, reduce the amount needed by 1
                if element_type_needed[type_id] > 0:
                    element_type_needed[type_id] -= 1
            # If there is no space for them in XI, add to bench
            else:
                bench.loc[len(bench)] = my_elements_data.iloc[i, :]
        # If there is no space for them in XI, add to bench
        else:
            bench.loc[len(bench)] = my_elements_data.iloc[i, :]
    # Create df containing both starting XI and bench
    starting_xi = pd.concat([starting_xi, bench], ignore_index=True)
    starting_xi.rename(columns={'pp_1': 'gameweek_points'})
    return starting_xi
