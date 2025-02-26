import pandas as pd
import time
import warnings
from create_df_funcs import return_main_response, create_element_master, create_team_master, add_team_data, \
    predict_points
from fpl_2425.fpl_transfer_suggester.time_funcs import save_update_time, update_or_not
from time_funcs import return_current_gameweek
from suggest_elements import return_manager_stats, suggest_transfers, suggest_starting_xi

# show all columns and rows
pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

warnings.simplefilter(action='ignore', category=FutureWarning)


# TO RUN THE PROGRAM, NAVIGATE TO THE BOTTOM AND INPUT YOUR PARAMETERS INTO THE FUNCTION
def run_fpl_script(gw_comparison, force_update, manager_id):
    start_time_api = time.time()
    # Return's a json file from the fpl website, containing key data
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

    # If update is False
    if update_decision == False and force_update != True:
        # Obtain element_master (the main football player statistics df). Footballer players are referred to as elements
        element_master = pd.read_csv('element_master.csv')
        # Sort by the element with the highest predicted points (PP) in the specified range
        element_master.sort_values(by=f'pp_{gw_comparison}', inplace=True, ascending=False)
        # Creates dataframe containing team data (e.g. team xg, team xgc, team names, etc)
        team_master = create_team_master(element_master)
        print('The file \"element_master\" exists and is up to date :)')

    # If update is True
    elif update_decision or force_update:
        # Save the time that the last update started, so we can reference this the next time we run the program
        save_update_time()
        # Connect to FPL API and fetch element data
        element_master = create_element_master(main_response, current_gameweek)
        # Creates dataframe containing team data (e.g. team xg, team xgc, team names, etc)
        team_master = create_team_master(element_master)
        # Merge team data onto each element
        element_master = add_team_data(team_master, element_master)
        # Predict each elements points across the next 7 fixtures
        element_master = predict_points(team_master, element_master, gw_comparison)
        # Print time take to update
        print("--- Data Upload Run Time: %s seconds ---" % (time.time() - start_time_api))

    else:
        # If you didn't put True or False as 'force_update' parameter
        print('You need to input True or False.')
        exit()
    start_time_calc = time.time()
    # Return fpl managers team and bank based on 'manager_id' parameter
    manager_elements, manager_bank = return_manager_stats(manager_id, current_gameweek)
    # Suggest transfers for same manager
    suggested_transfers = suggest_transfers(manager_elements, manager_bank, element_master, gw_comparison)
    # Suggest starting eleven for same manager
    starting_xi = suggest_starting_xi(manager_elements, element_master)
    # Show the 100 best elements
    print(element_master.head(100))
    # Show each teams data
    print(team_master[team_master['team_id'] != 0])
    # Show suggested transfers
    print(suggested_transfers)
    # Show suggested starting 11
    print(starting_xi)
    # If you want to see a specific player's statistics and predicted points, write out the code as follows:
    print(element_master[element_master['web_name']=='Wan-Bissaka'])
    print(element_master[element_master['web_name']=='O.Dango'])
    print(element_master[element_master['web_name']=='Cunha'])
    print(element_master[element_master['web_name']=='Bowen'])
    print(element_master[element_master['web_name']=='Rashford'])






    print("--- Calc Run Time: %s seconds ---" % (time.time() - start_time_calc))


# Input parameters here to run the script
#   gw_comparison: the range of gameweeks you would like to see the elements with the highest predicted points for
#   force_update: forcefully update the data now? (it ill automatically update after every fixture or 12 hours)
#   manager_id: the id of the manager to suggest transfers for. If you don't know how to find this, read README.md
run_fpl_script(gw_comparison=2, force_update=True, manager_id=705204)
