import sys
import numpy as np
import pandas as pd


from time_funcs import return_current_gameweek


def return_next_seven_opponents(element_team, element_fixtures, cgw):
    # not including fixtures from the current gameweek that haven't finished yet
    element_fixtures = element_fixtures[element_fixtures.event != cgw]
    home_fixtures = element_fixtures.team_h.to_list()
    away_fixtures = element_fixtures.team_a.to_list()
    next_seven_fixtures = []
    for i in range(7):
        if element_team == home_fixtures[i]:
            next_seven_fixtures.append(away_fixtures[i])
        else:
            next_seven_fixtures.append((home_fixtures[i]))
    return next_seven_fixtures


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
