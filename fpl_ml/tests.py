import pandas as pd
import numpy as np
from fpl_2425.fpl_transfer_suggester.time_funcs import return_current_gameweek
from fpl_2425.fpl_transfer_suggester.fpl_api_funcs import return_main_response


pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)

gls = pd.read_csv('data/2024-25_goals_scored.csv')
mins = pd.read_csv('data/2024-25_minutes.csv')
mr = return_main_response()
cgw = return_current_gameweek(mr)

input_features = [f'goals_{i+1}' for i in range(15)]
target_feature = ['expected_goals']  # change to whatever you're predicting

X = pd.DataFrame(columns=input_features)
y = pd.DataFrame(columns=target_feature)
window_size = 15


for i in range(0, len(gls.columns) - window_size):
    X_values = gls.iloc[:, i:i + window_size]
    y_values = gls.iloc[:, i + window_size]
    X_values.columns = input_features
    y_values.columns = target_feature
    X = pd.concat(objs=[X, X_values], axis=0)
    y = pd.concat(objs=[y, y_values], axis=0)

X.reset_index(inplace=True)
X.drop(columns=["index"], inplace=True)
print(X)


# g = pd.DataFrame(X)
# print(g)
# # The target is the target_feature from the next (16th) week
# target = df[target_feature].iloc[i + window_size]
# y.append(target)
#
# X = np.array(X)  # shape: (samples, 15 * num_features)
# y = np.array(y)  # shape: (samples,)

# X_data = []
# X_data.append(gls.iloc[:, 0:16].values.flatten())
#
#
# print(X_data)

# zero_proportion = (mins == 0).sum(axis=1) / mins.shape[1]
#
# mask = zero_proportion <= 0.5
#
# gls_filtered = gls[mask]
#
# print(gls_filtered[gls_filtered['name'] == 'Rodrigo \'Rodri\' Hernandez'])
