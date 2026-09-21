import os
import sys
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Ensure root ml-service is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def get_match_file_splits(data_directory="./training_data", test_size=0.2, random_state=42):
    all_files = [os.path.join(data_directory, f) for f in os.listdir(data_directory) if f.endswith('.csv')]
    
    if not all_files:
        raise FileNotFoundError(f"No processed data files found in {data_directory}. Please run your data preparer first.")
        
    train_files, test_files = train_test_split(all_files, test_size=test_size, random_state=random_state)
    
    print(f"Found {len(all_files)} parsed match datasets.")
    print(f"Splitting into {len(train_files)} training matches and {len(test_files)} testing matches.")
    
    return train_files, test_files

def load_combined_dataset(file_list):
    if not file_list:
        return pd.DataFrame()
    df_list = [pd.read_csv(fp) for fp in file_list]
    return pd.concat(df_list, axis=0, ignore_index=True)

def train_pitch_evaluator(data_path="./training_data", model_save_path="pitch_evaluator.json"):
    train_files, test_files = get_match_file_splits(data_path)
    
    print("Loading training data into memory...")
    train_df = load_combined_dataset(train_files)
    
    print("Loading test data into memory...")
    test_df = load_combined_dataset(test_files)
    
    target_col = "Target_Goal_Value"
    
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]
    
    X_test = test_df.drop(columns=[target_col])
    y_test = test_df[target_col]
    
    feature_names = X_train.columns.tolist()
    print(f"Features count: {len(feature_names)}")
    print(f"Final Dataset Shape -> Training set: {X_train.shape[0]} frames. Test set: {X_test.shape[0]} frames.")

    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        early_stopping_rounds=30
    )

    print("\nTraining XGBoost pitch state evaluation engine...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50
    )

    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print("\n--- Pipeline Evaluation Metrics ---")
    print(f"Mean Squared Error (MSE): {mse:.4f}")
    print(f"R-squared Score (Variance Explained): {r2:.4f}")

    model.save_model(model_save_path)
    print(f"\nModel architecture successfully saved to: {model_save_path}")
    return model

if __name__ == "__main__":
    trained_engine = train_pitch_evaluator()