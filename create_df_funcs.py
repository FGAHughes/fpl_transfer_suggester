import pandas as pd
import requests
import numpy as np

from indv_stat_funcs import return_opponents_in_next_seven_gws, past_x_performances

# show all columns
pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)


# A function that returns a JSON file from the FPL website
def return_main_response():
    main_response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
    return main_response


# a function to fetch and return the main element df (element_master) if update was True
def create_element_master(main_response, current_gameweek):
    # Update status
    print('element_master is under construction...')
    # Normalise and return main element df
    element_master = pd.json_normalize(main_response.json(), record_path='elements')
    # Select useful columns
    element_master = element_master[['id',
                                     'web_name',
                                     'team',
                                     'element_type',
                                     'chance_of_playing_next_round',
                                     'now_cost',
                                     'status']]
    # Add another column called ID which refers to an element's index and rename the preexisting ID as og_id as elements
    # are ordered by Teams and og_id is not
    element_master.insert(loc=1, column='og_id', value=element_master.id)
    element_master.reset_index(drop=True, inplace=True)
    element_master['id'] = element_master.index

    # create lists to hold element data
    all_element_stats = []
    all_element_fixtures = []
    # Track the team of the element whose data was just added, so we don't need to fetch the same fixtures each time
    previous_element_team = None
    # List to check for duplicate elements, which was a problem once when a real life transfer was incorrectly added
    elements_added = []
    # Add data for each element
    for element in range(len(element_master)):
        element_og_id = element_master.og_id[element]
        element_team = element_master.team[element]
        # Connect to FPL API and return dfs for each element's fixtures and stats
        element_fixtures_df, element_stats_df = create_element_dfs(element_og_id)
        element_fixtures_df.to_csv(f'csvs/element_fixtures/{element}_fix.csv', index=False)
        element_fixtures_df.to_csv(f'csvs/element_history/{element}_hist.csv', index=False)
        # Ensures df isn't empty, which can happen if a newly signed player has just been added to FPL
        if element_stats_df.empty:
            element_stats = [0, 0, 0, 0, 0, 0, 0]
        else:
            # A function to return an elements stats on average across their last x fixtures (recommended range is 9)
            element_stats = past_x_performances(element_stats_df, 7)
        # If the previous and current elements doesn't share a team
        if element_team != previous_element_team:
            # return element's fixtures across the next 7 gws
            element_fixtures = return_opponents_in_next_seven_gws(element_team, element_fixtures_df, current_gameweek)
        else:
            pass
        # Add stats and fixtures to equivalent lists
        all_element_stats.append(element_stats)
        all_element_fixtures.append(element_fixtures)
        # Set previous elements team to current elements team
        previous_element_team = element_team
        # Update progress every 100 elements
        if ((element % 100) == 0) and element != 0:
            print(f'The data of {element} elements has been added.')
        # If there is a duplicate, notify
        if element_master.id[element] in elements_added:
            print('Duplicate: ', element_master.id[element])
        # Add element to element's added list
        elements_added.append(element_master.id[element])
    # Convert to Numpy arrays so that we can add to element_master columns
    all_element_stats = np.asarray(all_element_stats, dtype='object')
    all_element_fixtures = np.asarray(all_element_fixtures, dtype='object')
    # Add lists to element_master
    element_master[['xg_value', 'xa_value', 'xgc_value', 'saves', 'minutes', 'starts', 'bonus']] = all_element_stats
    element_master[['fix1a', 'fix1b',
                    'fix2a', 'fix2b',
                    'fix3a', 'fix3b',
                    'fix4a', 'fix4b',
                    'fix5a', 'fix5b',
                    'fix6a', 'fix6b',
                    'fix7a', 'fix7b'
                    ]] = all_element_fixtures
    # Point calculations depend on element positions so add multipliers to determine this
    element_master = add_positional_multipliers(element_master)
    # If an element hasn't been injured this season it will display NaN, so replace these with 100 so show fully fit
    element_master['chance_of_playing_next_round'] = element_master['chance_of_playing_next_round'].fillna(100.0)
    element_master = element_master.fillna(0)
    print('\"element_master\" created')
    return element_master


# A function that adds multipliers to a dataframe depending on the element's position
def add_positional_multipliers(element_master):
    # Make a df of the positions and goal, assist and clean sheet multipliers for each position
    positional_multipliers = pd.DataFrame({'element_type': [1, 2, 3, 4],
                                           'goal_multi': [6, 6, 5, 4],
                                           'assist_multi': [3, 3, 3, 3],
                                           'cs_multi': [4, 4, 1, 0]})
    # Add these to each element in element_master
    updated_element_master = pd.merge(element_master, positional_multipliers, on='element_type')
    return updated_element_master


# A function that adds and element's team's data to a df
def add_team_data(team_master, element_master):
    # Add team data to df depending on the element's team
    element_master = element_master.merge(team_master, how='left', left_on='team', right_on='team_id')
    # Drop team ID as this is already on there
    element_master.drop(columns='team_id', inplace=True)
    # Rename these as team data will be added again for each fixture
    element_master = element_master.rename(columns={'team_xg': 'element_team_xg',
                                                    'team_xa': 'element_team_xa',
                                                    'team_xgc': 'element_team_xgc',
                                                    'team_name': 'element_team_name'
                                                    })
    return element_master


# A function to predict every element in element_masters points across 7 gws at once
def predict_points(team_master, element_master, gw_comparison):
    # For each gw, predict the points of the fixtures, accounting for blank and double gameweeks
    for gw in range(1, 8):
        element_master = predict_gameweek_points(element_master, team_master, gw, 'a')
        element_master = predict_gameweek_points(element_master, team_master, gw, 'b')
    # Add predict points for each gw together in new column
    for gw in range(1, 8):
        element_master = add_gw_predicted_points_column(element_master, gw)
    # Add columns for cumulative points for each gameweeks
    for gw in range(1, 8):
        element_master = add_cumulative_predict_points_column(element_master, gw)
    # Select only useful columns

    team_name_mapping = {
        1: 'ARS',  # Arsenal
        2: 'AVL',  # Aston Villa
        3: 'BOU',  # Bournemouth
        4: 'BRE',  # Brentford
        5: 'BRI',  # Brighton & Hove Albion (or BHA)
        6: 'BUR',  # Burnley
        7: 'CHE',  # Chelsea
        8: 'CRY',  # Crystal Palace
        9: 'EVE',  # Everton
        10: 'FUL',  # Fulham
        11: 'LEE',  # Leeds United
        12: 'LIV',  # Liverpool
        13: 'MCI',  # Manchester City
        14: 'MUN',  # Manchester United
        15: 'NEW',  # Newcastle United
        16: 'NFO',  # Nottingham Forest
        17: 'SUN',  # Sunderland
        18: 'TOT',  # Tottenham Hotspur
        19: 'WHU',  # West Ham United
        20: 'WOL',  # Wolverhampton Wanderers
        0: None  # or any fallback
    }

    for i in range(1, 8):
        element_master[f'fix{i}a'] = element_master[f'fix{i}a'].map(team_name_mapping)
        element_master[f'fix{i}b'] = element_master[f'fix{i}b'].map(team_name_mapping)
        element_master[f'fix{i}'] = element_master.apply(lambda row: [row[f'fix{i}a'], row[f'fix{i}b']] if row[f'fix{i}b'] is not None else row[f'fix{i}a'], axis=1)

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
                                     'fix1',
                                     'fix2',
                                     'fix3',
                                     'fix4',
                                     'fix5',
                                     'fix6',
                                     'fix7',
                                     'pp_1',
                                     'pp_2',
                                     'pp_3',
                                     'pp_4',
                                     'pp_5',
                                     'pp_6',
                                     'pp_7'
                                     ]]
    # Convert to 2 decimal places
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
    # Sort by total points in the next x gameweeks
    element_master.sort_values(by=f'pp_{gw_comparison}', ascending=False, inplace=True)
    # Save to csv, so later we can fetch element_master without having to run the whole program each time
    element_master.to_csv('element_master.csv', index=False)
    return element_master


# A function to create a df containing team statistics and info
def create_team_master(element_master):
    # List that will be added to df as team data
    team_df = []
    # Appending team '0' which will be used for blank gameweeks
    team_df.append([0, 'BLANK', 0, 0, 0])
    # List of team names (shorthand)
    team_names = ['ARS', 'AVL', 'BOU', 'BRE', 'BRI', 'BUR', 'CHE', 'CRY', 'EVE', 'FUL', 'LEE',
                  'LIV', 'MCI', 'MUN', 'NEW', 'NFO', 'SUN', 'TOT', 'WHU', 'WOL']
    # Add list of info and stats per team to the list that will be added to df as team data
    for i in range(1, 21):
        team_row = []
        # Create df of each team's elements
        team_players = element_master.groupby('team').get_group(i)
        # Append team ID to list
        team_row.append(i)
        # Append team name (shorthand)
        team_row.append(team_names[i - 1])
        # Append team expected goals across the past x fixtures
        team_row.append((sum(team_players.xg_value)))
        # Append team expected assists
        team_row.append((sum(team_players.xa_value)))
        # Append team expected goals conceded
        team_row.append(max(team_players.xgc_value))  # THIS DOESN'T WORK BECAUSE WHAT IF THEY GET A RED CARD!!!!!!
        # Append team data to main team list
        team_df.append(team_row)
    # Create team df
    team_master = pd.DataFrame(team_df, columns=['team_id',
                                                 'team_name',
                                                 'team_xg',
                                                 'team_xa',
                                                 'team_xgc'
                                                 ])
    print('\"team_master\" created')
    return team_master


# A function that returns an element's upcoming fixtures and stats across previous fixtures
def create_element_dfs(element_original_id):
    element_response = requests.get(f'https://fantasy.premierleague.com/api/element-summary/{element_original_id}/')
    element_fixtures = pd.json_normalize(element_response.json(), record_path='fixtures')
    element_history = pd.json_normalize(element_response.json(), record_path='history')
    return element_fixtures, element_history


# A function that adds a predicted points per gameweek column to element master
def add_gw_predicted_points_column(element_master, gw):
    element_master[f'gw{gw}_pp'] = element_master[f'gw{gw}_ppa'] + element_master[f'gw{gw}_ppb']
    return element_master


# A function that adds a cumulative total of points column for each gameweek to element_master
def add_cumulative_predict_points_column(element_master, forecast_gameweeks):
    element_master[f'pp_{forecast_gameweeks}'] = 0
    for gw in range(1, forecast_gameweeks + 1):
        element_master[f'pp_{forecast_gameweeks}'] += element_master[f'gw{gw}_ppa'] + element_master[
            f'gw{gw}_ppb']

    return element_master


# A function to predict points for all elements at once each gameweek
# Note: parameter 'a_or_b' is used in case of double gws, with a being the first game and b being the second
def predict_gameweek_points(element_master, team_master, gameweek, a_or_b):
    # Name of fixture (e.g fix1b will be the second fixture in the gameweek that's one week away)
    upcomming_fixture = f'fix{gameweek}{a_or_b}'
    # Add each the team data for the opponent in the fixture
    element_master = element_master.merge(team_master, how='left', left_on=upcomming_fixture, right_on='team_id')
    # Calculate expected points from goals for each element in their fixture
    expected_goal_points = ((element_master.xg_value / element_master.element_team_xg
                             * (
                                     element_master.team_xgc + element_master.element_team_xg) / 2)) * element_master.goal_multi
    # Do the same for assist points
    expected_assist_points = ((element_master.xa_value / element_master.element_team_xg)
                              * ((
                                         element_master.team_xgc + element_master.element_team_xg) / 2)) * element_master.assist_multi
    # And for clean sheet points, using Poisson distribution to calc the probability that 0 goals are conceded
    expected_cs_points = 2.718281828459045 ** (
        -((element_master.element_team_xgc + element_master.team_xg) / 2)) * element_master.cs_multi
    # For now save points are just calculated by average saves, not adjusting for opponent factors, such as shots taken
    expected_save_points = element_master.saves / 3
    # Bonus is just added as average bonus per game
    expected_bonus = element_master.bonus
    # Add all expected points to column to calculate total expected points from actions
    element_master[f'gw{gameweek}_pp{a_or_b}'] = (expected_goal_points +
                                                  expected_assist_points +
                                                  expected_save_points +
                                                  expected_cs_points +
                                                  expected_bonus)
    # If avg minutes >= 60, add 2 minutes points, if 60 > avg minutes > 0, add 1, else, add 0
    element_master[f'gw{gameweek}_pp{a_or_b}'] = element_master.apply(
        lambda row: row[f'gw{gameweek}_pp{a_or_b}'] + 2 if row['minutes'] >= 60 else row[f'gw{gameweek}_pp{a_or_b}'] + 1
        if 0 < row['minutes'] < 60 else row[f'gw{gameweek}_pp{a_or_b}'], axis=1)
    # If element isn't fit, set predicted points to 0
    element_master[f'gw{gameweek}_pp{a_or_b}'] = element_master.apply(
        lambda row: 0 if (row['chance_of_playing_next_round'] < 75 or row['starts'] < 1) else row[
            f'gw{gameweek}_pp{a_or_b}'], axis=1)
    # If the fixture is blank or there is no double, set the predicted points to 0
    element_master[f'gw{gameweek}_pp{a_or_b}'] = element_master.apply(
        lambda row: 0 if row[f'fix{gameweek}{a_or_b}'] == 0 else row[f'gw{gameweek}_pp{a_or_b}'], axis=1)
    # Remove columns that were only used for calcs
    element_master.drop(columns=['team_xg', 'team_xa', 'team_xgc', 'team_id', 'team_name'], inplace=True)
    return (element_master)
