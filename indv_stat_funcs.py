import sys
import numpy as np
import pandas as pd


from time_funcs import return_current_gameweek


def return_next_seven_opponents(element_team, element_fixtures, cgw):
    # not including fixtures from the current gameweek that haven't finished yet
    element_fixtures = element_fixtures[element_fixtures.event != cgw]
    element_fixtures.reset_index(inplace=True)
    home_fixtures = element_fixtures.team_h.to_list()
    away_fixtures = element_fixtures.team_a.to_list()
    fixtures = []
    row_index = -1
    # There is no previous gw in the fixture df, so we set it as what would be the previous gameweek
    while len(fixtures) < 14:
        row_index += 1
        if element_team == home_fixtures[row_index]:
            next_opponent = away_fixtures[row_index]
        else:
            next_opponent = home_fixtures[row_index]
        next_gameweek = element_fixtures.event[row_index]
        # for each fixture, find out what the fixture after it as well
        try:
            following_gameweek = element_fixtures.event[row_index + 1]
        # if there is no fixture after, then fill up the rest of the list with 0s
        except KeyError:
            [fixtures.append(0) for x in range(14 - len(fixtures))]
            break
        if next_gameweek > cgw + 1:
            [fixtures.append(0) for x in range(2*(next_gameweek-cgw-1))]
        fixtures.append(next_opponent)
        # then if the next fixture isn't the same as the current gameweek, append a 0
        if following_gameweek > next_gameweek and next_gameweek != cgw:
             fixtures.append(0)
        cgw = next_gameweek
    if len(fixtures) > 14:
        fixtures = fixtures[0:14]
    return fixtures


def past_x_performances(element_history, x):
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
    element_history['xg_value'] = (element_history.goals_scored + element_history.expected_goals) / 2
    element_history['xa_value'] = (element_history.assists + element_history.expected_assists) / 2
    element_history['xgc_value'] = (element_history.goals_conceded + element_history.expected_goals_conceded) / 2
    element_history = element_history[['xg_value',
                                       'xa_value',
                                       'xgc_value',
                                       'saves',
                                       'minutes',
                                       'starts',
                                       'bonus']]
    previous_x_fix_stats = return_n_rows_from_bottom(x, element_history)
    sum_previous_seven_fix = previous_x_fix_stats.sum(axis=0).to_list()
    games_played = previous_x_fix_stats[previous_x_fix_stats['minutes'] > 0].count()[4]
    if games_played > 0:
        avg_stats_across_x = [x / games_played for x in sum_previous_seven_fix]
        avg_stats_across_x[5] = sum_previous_seven_fix[5]
    else:
        avg_stats_across_x = [0, 0, 0, 0, 0, 0, 0]
    return avg_stats_across_x


def return_n_rows_from_bottom(n, df):
    if len(df) >= n:
        bottom = len(df)
        n_from_bottom = len(df) - n
        element_statistics = df.iloc[n_from_bottom:bottom, :]
    else:
        element_statistics = df.iloc[:, :]
    n_rows = element_statistics
    return n_rows

# def decide_home_fixture(array):
#     if previous_fixture != fixtures[i] and:
#         if home_fixtures[i] == element_team:
#             next_seven_fixtures.append([away_fixtures[i]])
#         else:
#             next_seven_fixtures.append(home_fixtures[i])
