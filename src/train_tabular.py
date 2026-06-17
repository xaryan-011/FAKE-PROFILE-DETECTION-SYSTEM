"""
Train the XGBoost tabular model and the Isolation Forest anomaly detector.
Outputs: models/tabular_model.pkl, models/anomaly_model.pkl
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.ensemble import IsolationForest
from xgboost import XGBClassifier
import joblib

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.features import extract_features, FEATURE_NAMES


def prepare_features(df):
    """Extract features from every profile in the dataframe."""
    feature_rows = []
    for _, row in df.iterrows():
        profile = row.to_dict()
        feats = extract_features(profile)
        feature_rows.append([feats[name] for name in FEATURE_NAMES])
    return pd.DataFrame(feature_rows, columns=FEATURE_NAMES)


def train(df_input=None):
    # Load dataset
    if df_input is None:
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "profiles.csv")
        df = pd.read_csv(data_path)
    else:
        df = df_input
        
    print(f"[DATA] Loaded {len(df)} profiles for tabular training")

    # Extract features
    print("[FEATURES] Extracting features...")
    X = prepare_features(df)
    y = df["is_fake"]

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"   Train: {len(X_train)}, Test: {len(X_test)}")

    # Hyperparameter search for XGBoost
    print("[SEARCH] Running hyperparameter search...")
    param_grid = {
        "n_estimators": [100, 200],
        "max_depth": [4, 6, 8],
        "learning_rate": [0.05, 0.1],
        "subsample": [0.8, 1.0],
    }

    model = XGBClassifier(
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
    )

    grid_search = GridSearchCV(
        model, param_grid,
        cv=3, scoring="f1", n_jobs=-1, verbose=0
    )
    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_
    print(f"[SUCCESS] Best params: {grid_search.best_params_}")

    # Evaluate XGBoost
    y_pred = best_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    print(f"\n[METRICS] Accuracy: {accuracy:.4f}")
    print("\n[REPORT] Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Real", "Fake"]))

    # Feature importance
    importances = best_model.feature_importances_
    feat_imp = sorted(zip(FEATURE_NAMES, importances), key=lambda x: x[1], reverse=True)
    print("[IMPORTANCE] Top 10 Features:")
    for name, imp in feat_imp[:10]:
        print(f"   {name}: {imp:.4f}")

    # Train Unsupervised Isolation Forest
    print("\n[ANOMALY] Training Unsupervised Isolation Forest Anomaly Detector...")
    anomaly_model = IsolationForest(
        n_estimators=150,
        contamination=0.1,  # Expected proportion of outliers (fakes)
        random_state=42
    )
    # Fit only on the training features (X_train)
    anomaly_model.fit(X_train)
    
    # Save models
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, "tabular_model.pkl")
    anomaly_path = os.path.join(models_dir, "anomaly_model.pkl")
    
    joblib.dump(best_model, model_path)
    joblib.dump(anomaly_model, anomaly_path)
    
    print(f"[SAVE] Tabular model saved -> {model_path}")
    print(f"[SAVE] Anomaly model saved -> {anomaly_path}")

    return {
        "accuracy": float(accuracy),
        "f1_score": float(f1),
        "best_params": grid_search.best_params_,
        "feature_importances": [[name, float(imp)] for name, imp in feat_imp[:10]]
    }


if __name__ == "__main__":
    train()
