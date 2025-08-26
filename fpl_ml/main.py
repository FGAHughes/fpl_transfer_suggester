from step1_pandas_stuff import reorganise_data
from step2_regression_stuff import prepare_data

years = ['2022-23', '2023-24', '2024-25']

df = reorganise_data(years)
df = prepare_data(df)
print(df)

