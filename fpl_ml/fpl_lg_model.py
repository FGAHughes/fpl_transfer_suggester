import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

def fpl_lg(X_df, y_df):
    # Example: Assuming your DataFrame is already loaded
    # Replace this with your actual data loading step
    # df = pd.read_csv("your_data.csv")

    # Feature columns: 54 columns from your description
    feature_cols = X_df.columns

    # Target variable: for example, player's goals in match 10
    target_col = y_df.columns

    # Split features and target
    X = X_df[feature_cols]
    y = y_df[target_col]

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # Fit Ridge Regression
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)

    # Coefficients and mapping to feature names
    coeffs = pd.Series(model.coef_, index=feature_cols).sort_values(ascending=False)

    # Display top positive and negative predictors
    print("🔼 Top Positive Coefficients:")
    print(coeffs.head(10))

    print("\n🔽 Top Negative Coefficients:")
    print(coeffs.tail(10))

