from clean_data import create_clean_dfs
from reformat_dfs import create_att_df, clean_att_df, combine_year_data, prepare_prediction_data
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from fpl_lg_model import fpl_lg



attributes = ['goals_scored', 'expected_goals', 'assists', 'expected_assists', 'goals_conceded',
              'expected_goals_conceded', 'minutes', 'opponent_team']
years = ['2022-23', '2023-24', '2024-25']

for year in years:
    for att in attributes:
        create_att_df(year, att)

for year in years:
    for att in attributes:
        clean_att_df(year, att)

for attribute in attributes:
    combine_year_data(attribute, years)

X_data, y_data, qual_data = prepare_prediction_data(attributes[0], attributes[1], attributes[4], attributes[5])
#
# X_train, X_test, y_train, y_test = train_test_split(X_data, y_data, test_size=0.1, random_state=42)
#
# model = LinearRegression()
#
# model.fit(X_train, y_train)
#
# y_pred = model.predict(X_test)
#
# print("Intercept:", model.intercept_)
# print("Coefficients:", model.coef_)
#
# X_data.loc[len(X_data)] = model.coef_[0]
#
# print(X_data)


fpl_lg(X_data, y_data)







