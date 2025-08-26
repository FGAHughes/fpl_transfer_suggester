from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
import pandas as pd
from step1_pandas_stuff import reorganise_data, return_col_names
import xgboost as xgb
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error
from imblearn.under_sampling import RandomUnderSampler
from sklearn.utils import resample


# years = ['2022-23', '2023-24', '2024-25']
# df = reorganise_data(years)


def prepare_data(df):
    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    encoded_array = encoder.fit_transform(df[['position']])
    encoded_df = pd.DataFrame(encoded_array, columns=encoder.get_feature_names_out(['position']), index=df.index)
    df = pd.concat([df.drop('position', axis=1), encoded_df], axis=1)
    return df

def make_collated_cols(df, att):
    # df[f'{att}_in_last_1_games'] = df[f'gw7_{att}']
    df[f'{att}_in_last_3_games'] = df[f'gw7_{att}'] + df[f'gw6_{att}'] + df[f'gw5_{att}']
    df[f'{att}_in_last_5_games'] = df[f'gw7_{att}'] + df[f'gw6_{att}'] + df[f'gw5_{att}'] + df[f'gw4_{att}'] + df[f'gw3_{att}']
    df[f'{att}_in_last_7_games'] = df[f'gw7_{att}'] + df[f'gw6_{att}'] + df[f'gw5_{att}'] + df[f'gw4_{att}'] + df[f'gw3_{att}'] + df[f'gw2_{att}'] + df[f'gw1_{att}']
    if att == 'minutes':
        divisor = {3: 270, 5: 450, 7: 630}
        for n in (3, 5, 7):
            df[f'mins_rate_last_{n}'] = df[f'minutes_in_last_{n}_games'] / divisor[n]
    return df


def xgbreg_goals_scored(df):
    df = df[df['position_GK'] != 1]
    df = df.drop(columns=['position_GK'])
    y = df['gw8_goals_scored']
    X = df.copy()
    X = df.drop([col for col in df.columns if col.startswith('gw8')], axis=1)
    X = X.drop([col for col in X.columns if col.endswith('goals_conceded') and 'opp__' not in col], axis=1)
    X = X.drop([col for col in X.columns if (col.endswith('goals_scored') or col.endswith('expected_goals'))and 'opp__' in col], axis=1)
    X = X.drop([col for col in X.columns if col.endswith('assists')], axis=1)
    # X = X.drop([col for col in X.columns if col.endswith('was_home')], axis=1)
    X = make_collated_cols(X, 'goals_scored')
    X = make_collated_cols(X, 'expected_goals')
    X = make_collated_cols(X, 'opp__goals_conceded')
    X = make_collated_cols(X, 'opp__expected_goals_conceded')
    X = make_collated_cols(X, 'minutes')
    X = X.drop(columns=[c for c in X.columns if c.startswith('gw8')], errors='ignore')

    # Combine X and y into one DataFrame
    df_full = X.copy()
    df_full['target'] = y

    # Separate by class
    df_0 = df_full[df_full['target'] == 0]
    df_1 = df_full[df_full['target'] == 1]
    df_2 = df_full[df_full['target'] == 2]
    df_3 = df_full[df_full['target'] == 3]

    # Undersample the 0-goal class
    df_0_under = resample(df_0,
                          replace=False,  # sample without replacement
                          n_samples=len(df_1),  # match class 1
                          random_state=42)

    # Combine all together
    df_balanced = pd.concat([df_0_under, df_1, df_2, df_3])

    # Shuffle the resulting dataset
    df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)

    # Separate back into X and y
    X = df_balanced.drop('target', axis=1)
    y = df_balanced['target']

    # rus = RandomUnderSampler(random_state=0)
    # X, y = rus.fit_resample(X, y)

    print(y.value_counts())  # Distribution of gw8_goals_scored
    print(y.describe())  # Mean/variance
    print((y > 0).mean())  # % with ≥1 goal
    # split data into testing and training data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    # Using sklearn API for simplicity
    model = xgb.XGBRegressor(
        verbosity=0,  # Controls the number of messages printed by xgb, with 0 being silent, 1 warnings, 2 info and 3 debug
        objective='reg:squarederror',  # tells the model what it's trying to min/maximise while learning. This tells XGBoost to use squared error loss for regression.Calculated by (Y_actual - Y_predicted)^2
        random_state=42,
        colsample_bytree=0.8,  # Fraction of features used when building each tree
        learning_rate=0.01,  # Shrinks the contribution of each tree, with lower values making it more conservative (and maybe realistic)
        subsample=0.8  # Fraction of subsamples
    )
    # A dictionary of parameters for grid_search to search over and try. It will try all combinations with all parameters
    param_grid = {
        'max_depth': [3, 5, 7],  # max depth of each decision tree, as before.
        # you had learning rates of 0.01, 0.1 and 0.2 for future reference, it just always picked 0.01
        'n_estimators': [200, 500],  # Total number of trees built
        'subsample': [0.8, 1.0],  # Fraction of subsamples
        'min_child_weight': [1, 5, 10],  #Controls how small a group can be before it splits the data (aka don't split a tree branch unless there's enough data)
        'reg_alpha': [0.5, 1],  # Control the influence of unimportant features, with 1 shrinking their influence to 0
        'reg_lambda': [1, 2, 5]  # Prevents the model from giving too much influence to any one feature, reducing overfitting, with higher values reducing overfitting
    }

    # perform cross validation to increase training data
    cv = KFold(n_splits=3,  # The number of times the data is split and the number of times the model is trained on this
               shuffle=True,
               random_state=42
               )
    grid_search = GridSearchCV(estimator=model,  # The machine learning model you want to train
                               param_grid=param_grid,
                               scoring='neg_mean_squared_error',  # This is how grid search decides the best set of params, in this case it is aiming for the lower mean squared error (same equation as before)
                               cv=cv,
                               verbose=1,
                               n_jobs=-1  # used all available CPU cores to parallelize the job
                               )
    grid_search.fit(X_train, y_train)
    model = grid_search.best_estimator_

    model.fit(X_train, y_train,
              eval_set=[(X_test, y_test)],  # training data
              verbose=1  # same as before

              )
    train_r2_score = model.score(X_train, y_train)
    test_r2_score = model.score(X_test, y_test)

    print('train score: ', train_r2_score)
    print('test score: ', test_r2_score)
    print('Best paratmeters: ', grid_search.best_params_)
    y_pred = model.predict(X_test)
    print("MAE:", mean_absolute_error(y_test, y_pred))
    print("RMSE:", mean_squared_error(y_test, y_pred))
    xgb.plot_importance(model)
    plt.show()

# df = prepare_data(df)
# xgbreg_goals_scored(df)
