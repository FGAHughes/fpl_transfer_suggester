import xgboost
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
import pandas as pd
from step1_pandas_stuff import reorganise_data, return_col_names
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, classification_report
from imblearn.under_sampling import RandomUnderSampler
from sklearn.utils import resample
from step2_regression_stuff import prepare_data, make_collated_cols
from xgboost import XGBClassifier
from xgboost import plot_importance


years = ['2022-23', '2023-24', '2024-25']

df = reorganise_data(years)
df = prepare_data(df)
df.to_csv('data_master.csv', index=False)


def xgbclass_goals_scored(df):

    df = df[df['position_GK'] != 1]
    df = df.drop(columns=['position_GK'])

    df['scored'] = (df['gw8_goals_scored'] > 0).astype(int)
    y = df['scored']
    df = df.drop(columns=['scored'])
    X = df.copy()
    X = X.drop([col for col in X.columns if (col.startswith('gw8') and not col.endswith('was_home'))], axis=1)
    X = X.drop([col for col in X.columns if col.endswith('goals_conceded') and 'opp__' not in col], axis=1)
    X = X.drop([col for col in X.columns if
                (col.endswith('goals_scored') or col.endswith('expected_goals')) and 'opp__' in col], axis=1)
    X = X.drop([col for col in X.columns if col.endswith('assists')], axis=1)
    X = X.drop([col for col in X.columns if (col.endswith('was_home') and not col.startswith('gw8'))], axis=1)

    X = make_collated_cols(X, 'goals_scored')
    X = make_collated_cols(X, 'expected_goals')
    X = make_collated_cols(X, 'opp__goals_conceded')
    X = make_collated_cols(X, 'opp__expected_goals_conceded')
    X = make_collated_cols(X, 'minutes')
    X = X.drop(columns=[c for c in X.columns if c.startswith('gw') and not c.endswith('was_home')], errors='ignore')
    print(X.columns)
    rus = RandomUnderSampler(random_state=42)
    X, y = rus.fit_resample(X, y)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)
    model = XGBClassifier(
        verbosity=1,
        eval_metric='logloss'
    )
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1],
        'n_estimators': [100, 200],
        'subsample': [0.8, 1]
    }

    cross_validation = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    grid_search = GridSearchCV(estimator=model, param_grid=param_grid, scoring='f1_macro',
                               cv=cross_validation, verbose=1, n_jobs=-1)

    grid_search.fit(X_train, y_train)
    xgb = grid_search.best_estimator_
    predictions=xgb.predict(X_test)
    print(classification_report(y_test, predictions))
    print('best params: ', grid_search.best_params_)
    fig, ax = plt.subplots(figsize=(10, 8))
    plot_importance(xgb, importance_type='weight', max_num_features=50, ax=ax)
    ax.tick_params(axis='y', labelsize=8)
    plt.show()





xgbclass_goals_scored(df)