import pandas as pd
import os
import re

pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

years = ['2022-23', '2023-24', '2024-25']


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


def rename_col_headers_to_include_x(df, exceptions, x):
    cols = df.columns
    for i in range(len(cols)):
        if cols[i] not in exceptions:
            df = df.rename(columns={f'{cols[i]}': f'{x}_{cols[i]}'})
    return df


def rename_cols(df, renamed_cols):
    cols = [col for col in df.columns]
    for i in range(len(renamed_cols)):
        df = df.rename(columns={f'{cols[i]}': f'{renamed_cols[i]}'})
    return df


def create_team_df(df):
    df_team = df[['team', 'assists', 'expected_assists', 'goals_scored', 'expected_goals', 'goals_conceded',
                  'expected_goals_conceded']].groupby('team').agg(
        {'assists': 'sum',
         'expected_assists': 'sum',
         'goals_scored': 'sum',
         'expected_goals': 'sum',
         'goals_conceded': 'max',
         'expected_goals_conceded': 'max'}
    ).reset_index()
    df_team.sort_values(ascending=True, inplace=True, by='team')
    df_team['team'] = df_team.index + 1
    df_team = rename_col_headers_to_include_x(df_team, ['team'], f'opp_')
    df_team.rename(columns={'team': 'opponent_team'}, inplace=True)
    return df_team

def return_col_names():
    col_names = [
        'gw1_position', 'gw1_team', 'gw1_assists', 'gw1_expected_assists', 'gw1_goals_scored', 'gw1_expected_goals',
        'gw1_goals_conceded', 'gw1_expected_goals_conceded', 'gw1_opponent_team', 'gw1_minutes', 'gw1_was_home',
        'gw1_opp__assists', 'gw1_opp__expected_assists', 'gw1_opp__goals_scored', 'gw1_opp__expected_goals',
        'gw1_opp__goals_conceded', 'gw1_opp__expected_goals_conceded',
        'gw2_position', 'gw2_team', 'gw2_assists', 'gw2_expected_assists', 'gw2_goals_scored', 'gw2_expected_goals',
        'gw2_goals_conceded', 'gw2_expected_goals_conceded', 'gw2_opponent_team', 'gw2_minutes', 'gw2_was_home',
        'gw2_opp__assists', 'gw2_opp__expected_assists', 'gw2_opp__goals_scored', 'gw2_opp__expected_goals',
        'gw2_opp__goals_conceded', 'gw2_opp__expected_goals_conceded',
        'gw3_position', 'gw3_team', 'gw3_assists', 'gw3_expected_assists', 'gw3_goals_scored', 'gw3_expected_goals',
        'gw3_goals_conceded', 'gw3_expected_goals_conceded', 'gw3_opponent_team', 'gw3_minutes', 'gw3_was_home',
        'gw3_opp__assists', 'gw3_opp__expected_assists', 'gw3_opp__goals_scored', 'gw3_opp__expected_goals',
        'gw3_opp__goals_conceded', 'gw3_opp__expected_goals_conceded',
        'gw4_position', 'gw4_team', 'gw4_assists', 'gw4_expected_assists', 'gw4_goals_scored', 'gw4_expected_goals',
        'gw4_goals_conceded', 'gw4_expected_goals_conceded', 'gw4_opponent_team', 'gw4_minutes', 'gw4_was_home',
        'gw4_opp__assists', 'gw4_opp__expected_assists', 'gw4_opp__goals_scored', 'gw4_opp__expected_goals',
        'gw4_opp__goals_conceded', 'gw4_opp__expected_goals_conceded',
        'gw5_position', 'gw5_team', 'gw5_assists', 'gw5_expected_assists', 'gw5_goals_scored', 'gw5_expected_goals',
        'gw5_goals_conceded', 'gw5_expected_goals_conceded', 'gw5_opponent_team', 'gw5_minutes', 'gw5_was_home',
        'gw5_opp__assists', 'gw5_opp__expected_assists', 'gw5_opp__goals_scored', 'gw5_opp__expected_goals',
        'gw5_opp__goals_conceded', 'gw5_opp__expected_goals_conceded',
        'gw6_position', 'gw6_team', 'gw6_assists', 'gw6_expected_assists', 'gw6_goals_scored', 'gw6_expected_goals',
        'gw6_goals_conceded', 'gw6_expected_goals_conceded', 'gw6_opponent_team', 'gw6_minutes', 'gw6_was_home',
        'gw6_opp__assists', 'gw6_opp__expected_assists', 'gw6_opp__goals_scored', 'gw6_opp__expected_goals',
        'gw6_opp__goals_conceded', 'gw6_opp__expected_goals_conceded',
        'gw7_position', 'gw7_team', 'gw7_assists', 'gw7_expected_assists', 'gw7_goals_scored', 'gw7_expected_goals',
        'gw7_goals_conceded', 'gw7_expected_goals_conceded', 'gw7_opponent_team', 'gw7_minutes', 'gw7_was_home',
        'gw7_opp__assists', 'gw7_opp__expected_assists', 'gw7_opp__goals_scored', 'gw7_opp__expected_goals',
        'gw7_opp__goals_conceded', 'gw7_opp__expected_goals_conceded',
        'gw8_position', 'gw8_team', 'gw8_assists', 'gw8_expected_assists', 'gw8_goals_scored', 'gw8_expected_goals',
        'gw8_goals_conceded', 'gw8_expected_goals_conceded', 'gw8_opponent_team', 'gw8_minutes', 'gw8_was_home',
        'gw8_opp__assists', 'gw8_opp__expected_assists', 'gw8_opp__goals_scored', 'gw8_opp__expected_goals',
        'gw8_opp__goals_conceded', 'gw8_opp__expected_goals_conceded'
    ]
    return col_names


def reorganise_data(years):
    col_names = return_col_names()
    df_master = pd.DataFrame(columns=col_names)
    for year in years:
        max_gw = return_max_gameweek(
            f'/Users/felixhughes/Documents/repos/fpl/fpl_2425/fpl_transfer_suggester/fpl_ml/Fantasy-Premier-League/data/{year}/gws/')
        min_gameweek = 0

        for gw in range(1, max_gw + 1):
            # if first gameweek, create df including features that will be consistent across whole season
            data = pd.read_csv(
                f'/Users/felixhughes/Documents/repos/fpl/fpl_2425/fpl_transfer_suggester/fpl_ml/Fantasy-Premier-League/data/{year}/gws/gw{gw}.csv')
            data = data.infer_objects()
            if gw == 1 and data['expected_goals'].sum() == 0:
                df1 = pd.DataFrame(data['element'])
                min_gameweek+=1
            elif gw == 1 and data['expected_goals'].sum() > 0:
                df1 = data[['element', 'position', 'team', 'assists', 'expected_assists', 'goals_scored', 'expected_goals',
                            'goals_conceded', 'expected_goals_conceded', 'opponent_team', 'minutes', 'was_home']]
                df1['was_home'].replace({False: 0, True: 1}, inplace=True)
                df1_team = create_team_df(df1)
                df1 = df1.merge(df1_team, on='opponent_team', how='inner')
                df1 = rename_col_headers_to_include_x(df1, ['element'], f'gw{gw}')
            elif gw > 1 and data['expected_goals'].sum() > 0:
                df2 = data[['element', 'position', 'team', 'assists', 'expected_assists', 'goals_scored', 'expected_goals',
                            'goals_conceded', 'expected_goals_conceded', 'opponent_team', 'minutes', 'was_home']]
                df2['was_home'].replace({False: 0, True: 1}, inplace=True)
                df2 = df2.drop_duplicates(subset='element')
                df2_team = create_team_df(df2)
                df2 = df2.merge(df2_team, on='opponent_team', how='inner')
                df2 = rename_col_headers_to_include_x(df2, ['element'], f'gw{gw}')
                df1 = pd.merge(df1, df2, on='element', how='outer')
            else:
                min_gameweek+=1
        df1 = df1.drop(columns=['element'])
        att_per_gameweek = len(
            [col for col in df1.columns if col.startswith(f'gw{max_gw}_')])  # how many features are there per gameweek
        df = pd.DataFrame(columns=col_names)
        for i in range(max_gw-min_gameweek-7):
            data = df1.iloc[:, (att_per_gameweek * i):(att_per_gameweek * i) + (att_per_gameweek * 8)]
            data = rename_cols(data, col_names)
            df = pd.concat(objs=[df, data])
        team_columns = [col for col in df.columns if col.endswith('_team')]
        df = df.dropna()
        df = df[df[['gw1_minutes', 'gw2_minutes', 'gw3_minutes', 'gw4_minutes', 'gw5_minutes', 'gw6_minutes', 'gw7_minutes',
                    'gw8_minutes']].sum(axis=1) >  45*8]

        df_master = pd.concat(objs=[df_master, df])
    df_master.reset_index(inplace=True)
    df_master.drop(columns=['index'], inplace=True)
    position_columns = [col for col in df_master.columns if col.endswith('_position')]
    df_master['position'] = df_master[position_columns].bfill(axis=1).iloc[:, 0]
    df_master = df_master.drop(columns=position_columns)
    df_master = df_master.drop(columns=team_columns)

    return df_master

