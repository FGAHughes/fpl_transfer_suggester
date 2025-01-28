import pandas as pd
import requests
import datetime as datetime
import time
import warnings

# show all columns and rows
pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

warnings.simplefilter(action='ignore', category=FutureWarning)

from create_df_funcs import return_main_response, create_element_master, create_team_master, add_team_data, \
    predict_points, update_or_not, save_update_time

from time_funcs import return_current_gameweek, most_recent_fixture
from suggest_players import return_manager_stats, suggest_transfers, suggest_starting_xi


def run_fpl_script(gw_comparison, force_update, manager_id):
    start_time = time.time()
    # Return's a json file from the fpl website
    main_response = return_main_response()
    # A function to determine whether it has been 12 hours or a fixture has finished since the last update
    update_decision = update_or_not()
    # A function to return the current gameweek
    current_gameweek = return_current_gameweek(main_response)
    # Communicates update decision
    if update_decision or force_update:
        print('Update decision: ', True)
    else:
        print('Update decision:', False)

    # If not update,
    if update_decision == False and force_update != True:
        element_master = pd.read_csv('element_master.csv')
        element_master.sort_values(by=f'pp_{gw_comparison}', inplace=True, ascending=False)
        team_master = create_team_master(element_master)

        print('The file \"element_master\" exists and is up to date :)')

    elif update_decision == True or force_update == True:
        # Connect fpl API and fetch relevant dataframe
        save_update_time()
        element_master = create_element_master(main_response, current_gameweek)
        # element_master = pd.read_csv('element_master.csv')
        team_master = create_team_master(element_master)
        element_master = add_team_data(team_master, element_master)
        element_master = predict_points(team_master, element_master, gw_comparison)
        print("--- %s seconds ---" % (time.time() - start_time))

    else:
        print('You need to input True or False.')
        exit()
    manager_elements, manager_bank = return_manager_stats(manager_id, current_gameweek)
    suggested_transfers = suggest_transfers(manager_elements, manager_bank, element_master, gw_comparison)
    starting_xi = suggest_starting_xi(manager_elements, element_master)
    print(element_master.head(100))
    print(team_master)
    print(suggested_transfers)
    print(starting_xi)
    print("--- %s seconds ---" % (time.time() - start_time))


run_fpl_script(gw_comparison=5, force_update=False, manager_id=705204)
