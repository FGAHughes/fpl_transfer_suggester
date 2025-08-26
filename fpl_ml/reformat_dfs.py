import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import os
import re
import time

def return_max_gameweek(folder_path):
    # Regular expression to match 'gw' followed by a number and '.csv'
    pattern = re.compile(r'^gw(\d+)\.csv$')
    # Count matching files
    maximum = 0
    for filename in os.listdir(folder_path):
        match = pattern.match(filename)
        if match:
            number = int(match.group(1))
            if 1 <= number <= 38:
                maximum += 1
    return maximum

def create_att_df(year, attribute):
    # return folder with csvs
    path = f'/Users/felixhughes/Documents/repos/fpl/fpl_2425/fpl_transfer_suggester/fpl_ml/Fantasy-Premier-League/data/{year}/gws/'
    max_gw = return_max_gameweek(path)  # maximum gameweek of available data
    for gw in range(1, max_gw+1):
        # load this weeks data
        gameweek_data = pd.read_csv(
            f'/Users/felixhughes/Documents/repos/fpl/fpl_2425/fpl_transfer_suggester/fpl_ml/Fantasy-Premier-League/data/{year}/gws/gw{gw}.csv',
            encoding='latin-1')
        # make sure names are consistently formatted
        gameweek_data['name'] = gameweek_data['name'].str.strip()

        if gw == 1:  # if this is the first gameweek, create the attribute dataframe
            attribute_df = pd.DataFrame(gameweek_data[['name', 'team', 'position']])
            teams = sorted(gameweek_data['team'].unique())
            attribute_df['team'] = gameweek_data['team'].apply(lambda row: teams.index(row) + 1)
        new_columns = gameweek_data[['name', f'{attribute}']].copy() # copy attribute data
        new_columns.rename(columns={f'{attribute}': f'gw{gw}_{attribute}'}, inplace=True)  # rename to gw
        attribute_df = pd.merge(attribute_df, new_columns, how='outer', on='name')  # append to attribute dataframe
        attribute_df.drop_duplicates(subset=['name'], inplace=True)  # drop duplicate name column
    attribute_df.to_csv(f'data/att_dfs/{year}_{attribute}.csv', index=False)  # save to csv

def clean_att_df(year, attribute):
    # df to store data from all years
    every_year_data = pd.DataFrame(columns=[f'{attribute}_{x}' for x in range(1, 15)])

    # load useful data
    minutes_df = pd.read_csv(f'data/att_dfs/{year}_minutes.csv')
    attribute_df = pd.read_csv(f'data/att_dfs/{year}_{attribute}.csv')
    opponent_df = pd.read_csv(f'data/att_dfs/{year}_opponent_team.csv')

    opponent_df = fill_out_opponents(opponent_df)
    if attribute == 'opponent_team':
        attribute_df = fill_out_opponents(attribute_df)


    # # Remove players who haven't played at least half the fixtures
    # minutes_df.fillna(0, inplace=True)
    # blank_count = (minutes_df == 0).sum(axis=1) / minutes_df.shape[1]
    # minutes_mask = blank_count <= 0.75
    # attribute_df = attribute_df[minutes_mask]
    # minutes_df = minutes_df[minutes_mask]
    # opponent_df = opponent_df[minutes_mask]

    # store qualitative characteristics for reattachment later and remove for now
    qual_features = attribute_df[['name', 'team', 'position']]
    attribute_df.drop(columns=['name', 'team', 'position'], inplace=True)
    minutes_df.drop(columns=['name', 'team', 'position'], inplace=True)
    opponent_df.drop(columns=['name', 'team', 'position'], inplace=True)

    window_size = 11

    # # This was replacing missed fixtures with averages, but I don't think this works so I am removing for now
    # if attribute != 'opponent_team':
    #     # replace 0s with null
    #     minutes_df.columns = attribute_df.columns
    #     opponent_df.columns = attribute_df.columns
    #     attribute_df = attribute_df.where(minutes_df != 0)
    #     attribute_df = attribute_df.apply(lambda row: row.fillna(row.mean()), axis=1)

    # reformat dfs so there is a new row every 10 games, removing rows with a blank, creating team stat dfs as well
    input_features = [f'{attribute}_{i + 1}' for i in range(window_size)]
    input_features = qual_features.columns.to_list() + input_features
    attribute_df_new = pd.DataFrame(columns=input_features)
    opponent_df_new = pd.DataFrame(columns=input_features)
    team_df = pd.DataFrame(columns=input_features)
    team_df.drop(columns=['name', 'position'], inplace=True)

    for i in range(0, len(attribute_df.columns) - window_size):
        X_values = attribute_df.iloc[:, i:i + window_size]
        opp_X_values = opponent_df.iloc[:, i:i + window_size]
        X_values = pd.concat(objs=[qual_features, X_values], axis=1)
        opp_X_values = pd.concat(objs=[qual_features, opp_X_values], axis=1)
        X_values.columns = input_features
        opp_X_values.columns = input_features

        if attribute == 'opponent_team' or attribute == 'expected_goals_conceded' or attribute == 'goals_conceded':
            team_values = X_values.groupby('team', as_index=False).max(numeric_only=True)
        else:
            team_values = X_values.groupby('team', as_index=False).sum(numeric_only=True)
        team_values.loc[len(team_values)] = np.array(0 for i in range(window_size+1))
        # return opponents for gameweek we want to predict for
        next_opp = pd.DataFrame(data=opp_X_values.iloc[:, -1], index=opp_X_values.index)

        # ensure column names match for merge
        next_opp.rename(columns={f'{attribute}_{window_size}': 'team'}, inplace=True)
        # fill nan in opponent column
        next_opp.fillna(0, inplace=True)
        # merge on team
        next_opp = next_opp.merge(team_values, on='team', how='inner')
        attribute_df_new = pd.concat(objs=[attribute_df_new, X_values], axis=0)
        opponent_df_new = pd.concat(objs=[opponent_df_new, opp_X_values], axis=0)
        team_df = pd.concat(objs=[team_df, next_opp])
    # Remove rows where there has been a blank gameweek
    opponent_df_new.fillna(0, inplace=True)

    blank_count = (opponent_df_new == 0).sum(axis=1)
    blank_mask = blank_count != 0
    attribute_df_new = attribute_df_new[blank_mask]
    team_df.index = opponent_df_new.index
    team_df = team_df[blank_mask]

    # drop all rows with Nan


    attribute_df_new.to_csv(f'data/clean_att_dfs/{year}_{attribute}_clean.csv', index=False)
    team_df.to_csv(f'data/team_dfs/{year}_{attribute}_team.csv', index=False)

# yes, chatgpt wrote this
# yes, I have no idea how it works
def fill_out_opponents(opponent_df):
    opponent_columns = [col for col in opponent_df.columns if col.endswith('_opponent_team')]
    for col in opponent_columns:
        opponent_df[col] = opponent_df[col].fillna(
            opponent_df.groupby('team')[col].transform(
                lambda x: x.dropna().mode().iloc[0] if not x.dropna().empty else x))
    return opponent_df

def rename_col_names_to_att(df, attribute):
    cols = [col for col in df.columns]
    for i in range(10):
        df = df.rename(columns={f'{cols[i]}':f'{attribute}_{i+1}'})
    return df


# def make_team_dfs(year, attribute):
#     data = pd.read_csv(f'data/clean_att_dfs/{year}_{attribute}_clean.csv')
#     data.drop(columns=['name', 'position'], inplace=True)
#     if attribute == 'opponent_team' or attribute == 'expected_goals_conceded' or attribute == 'goals_conceded':
#         team_attribute_data = data.groupby('team', as_index=False).max(numeric_only=True)
#     else:
#         team_attribute_data = data.groupby('team', as_index=False).sum(numeric_only=True)
#     team_attribute_data.to_csv(f'data/team_dfs/{year}_{attribute}_team.csv', index=False)


def combine_year_data(attribute, years):
    iteration = 0
    for year in years:
        data = pd.read_csv(f'data/clean_att_dfs/{year}_{attribute}_clean.csv')
        team_data = pd.read_csv(f'data/team_dfs/{year}_{attribute}_team.csv')
        iteration += 1
        if iteration == 1:
            all_att_data = pd.DataFrame(columns=data.columns)
            all_team_data = pd.DataFrame(columns=team_data.columns)
        all_att_data = pd.concat(objs=[all_att_data, data], axis=0)
        all_team_data = pd.concat(objs=[all_team_data, team_data], axis=0)


    all_att_data.to_csv(f'data/combined_att_dfs/{attribute}.csv', index=False)
    all_team_data.to_csv(f'data/combined_att_dfs/{attribute}_team.csv', index=False)


def prepare_prediction_data(attribute, expected_attribute, opponent_attribute, expected_opponent_attribute):
    attributes = [f'{attribute}',
                  f'{expected_attribute}',
                  f'{attribute}_team',
                  f'{expected_attribute}_team',
                  f'{opponent_attribute}_team',
                  f'{expected_opponent_attribute}_team',
                  ]
    data = pd.read_csv(f'data/combined_att_dfs/{attributes[0]}.csv')
    qual_data = data.iloc[:, 0:3]
    X_data = data.iloc[:, -11:-1]
    y_data = data.iloc[:, -1:]
    for i in range(1, len(attributes)):
        data = pd.read_csv(f'data/combined_att_dfs/{attributes[i]}.csv')
        new_X_data = data.iloc[:, -11:-1]
        new_X_data = rename_col_names_to_att(new_X_data, attributes[i])
        X_data = pd.concat(objs=[X_data, new_X_data], axis=1)

    return X_data, y_data, qual_data




