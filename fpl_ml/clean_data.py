import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import os
import re
import time

from fpl_2425.fpl_transfer_suggester.os_funcs import make_directory

pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)


# pd.set_option('display.max_rows', None)


# A function that returns the number of gameweeks there is data for in the directory
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


# A function that creates a dataframe across attributes for a given range of seasons.
def create_overall_attribute_df(attribute, year_range):
    for year in year_range:
        max_gws = return_max_gameweek(
            f'/Users/felixhughes/Documents/repos/fpl/fpl_2425/fpl_transfer_suggester/fpl_ml/Fantasy-Premier-League/data/{year}/gws/')
        for gameweek in range(1, max_gws + 1):
            gameweek_data = pd.read_csv(
                f'/Users/felixhughes/Documents/repos/fpl/fpl_2425/fpl_transfer_suggester/fpl_ml/Fantasy-Premier-League/data/{year}/gws/gw{gameweek}.csv',
                encoding='latin-1')
            # make sure names are consistently formatted
            gameweek_data['name'] = gameweek_data['name'].str.strip()
            # xg in 2223 is only provided from gw16 onwards
            teams = sorted(gameweek_data['team'].unique())
            gameweek_data['team'] = gameweek_data['team'].apply(lambda row: teams.index(row) + 1)
            if gameweek == 1:
                attribute_df = pd.DataFrame(gameweek_data[['name']])
                team_df = pd.DataFrame(gameweek_data[['team']])
            # if every value in the column isn't Nan
            if not(gameweek_data[f'{attribute}'].isna().all()) or gameweek_data[f'{attribute}'].sum() != 0:
                if attribute == 'goals_conceded' or attribute == 'expected_goals_conceded':
                    team_gameweek_data = gameweek_data[['team', f'{attribute}']].groupby(['team']).max()
                elif attribute == 'opponent_team':
                    team_gameweek_data = gameweek_data[['team', f'{attribute}']].groupby(['team']).max()
                else:
                    team_gameweek_data = gameweek_data[['team', f'{attribute}']].groupby(['team']).sum()
                team_gameweek_data.rename(columns={f'{attribute}': f'gw{gameweek}_{attribute}'}, inplace=True)
                team_df = pd.merge(team_df, team_gameweek_data, how='outer', on='team')
                team_df.drop_duplicates(subset=['team'], inplace=True)

                new_columns = gameweek_data[['name', f'{attribute}']].copy()
                new_columns.rename(columns={f'{attribute}': f'gw{gameweek}_{attribute}'}, inplace=True)
                attribute_df = pd.merge(attribute_df, new_columns, how='outer', on='name')
                attribute_df.drop_duplicates(subset=['name'], inplace=True)
                # teams = sorted(gameweek_data['team'].unique())
                # gameweek_data['team'] = gameweek_data['team'].apply(lambda row: teams.index(row))
            else:
                print(attribute, year, gameweek)
        if attribute != 'opponent_team':
            team_df = team_df.apply(lambda row: row.fillna(row.mean()), axis=1)
        team_df.to_csv(f'data/raw_data/{year}_{attribute}_team.csv', index=False)
        attribute_df.to_csv(f'data/raw_data/{year}_{attribute}.csv', index=False)


def clean_and_restructure_dfs(attribute, year_range):
    all_year_data = pd.DataFrame(columns=[f'{attribute}_{x}' for x in range(1, 15)])
    team_all_year_data = pd.DataFrame(columns=[f'{attribute}_{x}' for x in range(1, 15)])

    for year in year_range:
        minutes_df = pd.read_csv(f'data/raw_data/{year}_minutes.csv')
        attribute_df = pd.read_csv(f'data/raw_data/{year}_{attribute}.csv')
        team_attribute_df = pd.read_csv(f'data/raw_data/{year}_{attribute}_team.csv')

        # Remove players who haven't played at least half the fixtures
        zero_proportion = (minutes_df == 0).sum(axis=1) / minutes_df.shape[1]
        mask = zero_proportion <= 0.5
        attribute_df = attribute_df[mask]
        minutes_df = minutes_df[mask]

        # ensure columns match
        minutes_df.columns = attribute_df.columns

        # # Store name column for later concatenation
        names = attribute_df[['name']]

        # Only keep numeric parts
        attribute_df.drop(columns='name', inplace=True)
        minutes_df.drop(columns='name', inplace=True)

        # attribute_df = attribute_df[minutes_df.value_counts(0)]
        # Apply mask
        attribute_df = attribute_df.where(minutes_df != 0)
        # if year == '2024-25' and attribute == 'goals_scored':
        #     print(attribute_df.iloc[67, :])

        # replace non starts with averages
        attribute_df = attribute_df.apply(lambda row: row.fillna(row.mean()), axis=1)
        input_features = [f'{attribute}_{i + 1}' for i in range(15)]

        attribute_df_new = pd.DataFrame(columns=input_features)
        team_attribute_df_new = pd.DataFrame(columns=input_features)
        window_size = 15

        for i in range(0, len(attribute_df.columns) - window_size):
            X_values = attribute_df.iloc[:, i:i + window_size]
            team_X_values = team_attribute_df.iloc[:, i:i + window_size]

            X_values.columns = input_features
            team_X_values.columns = input_features

            attribute_df_new = pd.concat(objs=[attribute_df_new, X_values], axis=0)
            team_attribute_df_new = pd.concat(objs=[team_attribute_df_new, team_X_values], axis=0)

        # X.reset_index(inplace=True)
        # X.drop(columns=["index"], inplace=True)

        # input_features = [f'goals_{i + 1}' for i in range(15)]
        # target_feature = ['expected_goals']  # change to whatever you're predicting
        #
        # X = pd.DataFrame(columns=input_features)
        # y = pd.DataFrame(columns=target_feature)
        # window_size = 15
        #
        # for i in range(0, len(attribute_df.columns) - window_size):
        #     X_values = attribute_df.iloc[:, i:i + window_size]
        #     y_values = attribute_df.iloc[:, i + window_size]
        #     X_values.columns = input_features
        #     y_values.columns = target_feature
        #     X = pd.concat(objs=[X, X_values], axis=0)
        #     y = pd.concat(objs=[y, y_values], axis=0)

        # X.reset_index(inplace=True)
        # X.drop(columns=["index"], inplace=True)

        # # Attach columns
        # attribute_df_copy = pd.concat([names, attribute_df], axis=1)

        all_year_data = pd.concat(objs=[all_year_data, attribute_df_new], axis=0)
        team_all_year_data = pd.concat(objs=[team_all_year_data, team_attribute_df_new], axis=0)
    print(team_all_year_data)
    all_year_data.to_csv(f'data/clean_data/{attribute}.csv', index=False)


def merge_dfs_on_rows(a_df, x_df):
    return pd.concat(objs=[a_df, x_df], axis=1)


def create_clean_dfs(decision):
    if decision:
        attributes = ['goals_scored', 'expected_goals', 'assists', 'expected_assists', 'goals_conceded',
                      'expected_goals_conceded', 'minutes', 'opponent_team']
        years = ['2022-23', '2023-24', '2024-25']

        # Create a df for each attribute
        for att in attributes:
            create_overall_attribute_df(att, years)

        for att in attributes:
            clean_and_restructure_dfs(att, years)

        for i in range(0, 6, 2):
            if attributes[i] == 'goals_scored' or attributes[i] == 'assists':
                merged_df = merge_dfs_on_rows(pd.read_csv(f'data/clean_data/{attributes[i]}.csv'),
                                              pd.read_csv(f'data/clean_data/{attributes[i + 1]}.csv')
                                              )
            merged_df.dropna(inplace=True)
            merged_df.to_csv(f'data/clean_data/{attributes[i]}_combined.csv')


