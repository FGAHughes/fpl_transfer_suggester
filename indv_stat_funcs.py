import sys
import numpy as np
import pandas as pd


from time_funcs import return_current_gameweek


# A function to return an elements opponents in the next 7 gameweeks
def return_opponents_in_next_seven_gws(element_team, element_fixtures, cgw):
    # Remove fixtures from the current gameweek that haven't finished yet
    element_fixtures = element_fixtures[element_fixtures.event != cgw]
    element_fixtures.reset_index(inplace=True)
    # Make lists of fixtures that can be used to identify the opponent by comparing against the element's team ID
    home_fixtures = element_fixtures.team_h  # to_list removed from here
    away_fixtures = element_fixtures.team_a  # to_list removed from here
    # Will store fixtures
    fixtures = []
    # Used to index rows and starts at -1 so that the first index is 0
    row_index = -1
    # The length of fixtures should be 14 as we want every fixture from the next 7 gameweeks, accounting for the fact
    # that there could be a double any week
    while len(fixtures) < 14:
        row_index += 1
        # Determine who the opponent is by knowing it is not the element's team
        if element_team == home_fixtures[row_index]:
            next_opponent = away_fixtures[row_index]
        else:
            next_opponent = home_fixtures[row_index]
        # The gameweek of the next fixtures
        next_gameweek = element_fixtures.event[row_index]
        # for each fixture, find out what the fixture after it as well, if there is one
        try:
            following_gameweek = element_fixtures.event[row_index + 1]
        # if there is no fixture after, then fill up the rest of the list with 0s to signify no fixtures
        except KeyError:
            [fixtures.append(0) for x in range(14 - len(fixtures))]
            break
        # if the gw of the next fixture is more than one gw away, add two 0s for every blank gameweek
        if next_gameweek > cgw + 1:
            [fixtures.append(0) for x in range(2*(next_gameweek-cgw-1))]
        # Add opponenet to fixtures list
        fixtures.append(next_opponent)
        # Then if the next fixture isn't the same as the current gameweek, append a 0 as it's not a double gw
        if following_gameweek > next_gameweek and next_gameweek != cgw:
             fixtures.append(0)
        # Store the gameweek we just used, so we can compare for the above
        cgw = next_gameweek
    # Depending on the gap between the second last and last gws, it may append too many 0s so we use this as a failsafe
    if len(fixtures) > 14:
        fixtures = fixtures[0:14]
    return fixtures


# A function to return the average statistics of each element across a given number of fixtures
def past_x_performances(element_history, x):
    # Select the stats we want averages for
    element_history = element_history[['goals_scored',
                                       'assists',
                                       'goals_conceded',
                                       'expected_goals',
                                       'expected_assists',
                                       'expected_goals_conceded',
                                       'saves',
                                       'minutes',
                                       'starts',
                                       'bonus'
                                       ]].astype(float)
    # For goals, assists and goals conceded, create a value that equals the average between actual and expecteds
    element_history['xg_value'] = (element_history.goals_scored + element_history.expected_goals) / 2
    element_history['xa_value'] = (element_history.assists + element_history.expected_assists) / 2
    element_history['xgc_value'] = (element_history.goals_conceded + element_history.expected_goals_conceded) / 2
    # Remove columns we just used to average
    element_history = element_history[['xg_value',
                                       'xa_value',
                                       'xgc_value',
                                       'saves',
                                       'minutes',
                                       'starts',
                                       'bonus']]
    # Return the element's last x fixtures
    element_history_x_gws = element_history.tail(x)
    element_starts = element_history_x_gws.sum(axis=0)[5]
    games_played = element_history_x_gws[element_history_x_gws['minutes'] != 0].count()[4]
    if games_played > 0:
        element_history_x_gws = element_history_x_gws[element_history_x_gws['minutes'] != 0]
        avg_stats_across_x = element_history_x_gws.mean()
        avg_stats_across_x[5] = element_starts
    else:
        avg_stats_across_x = [0, 0, 0, 0, 0, 0, 0]
    # # Create new list of fixtures that contains a sum of the elements stats in their past x fixtures
    # sum_previous_seven_fix = element_history_x_gws.sum(axis=0) # to_list removed from here
    # # Calculate the number of games they have played by counting fixtures in range x where their minutes > 0
    # games_played = element_history_x_gws[element_history_x_gws['minutes'] > 0].count()[4]
    # # If they played at least one game
    # if games_played > 0:
    #     # divide each stat by the number of games they played to find the average
    #     avg_stats_across_x = [x / games_played for x in sum_previous_seven_fix]
    #     # Add total starts back into the list, rather than average starts
    #     avg_stats_across_x[5] = sum_previous_seven_fix[5]
    # # If they played no games, set each stat to 0
    # else:
    #     avg_stats_across_x = [0, 0, 0, 0, 0, 0, 0]
    return avg_stats_across_x
