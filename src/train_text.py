"""
Train the NLP (TF-IDF + Logistic Regression) model on bio text.
Outputs: models/text_model.pkl, models/vectorizer.pkl
"""

import os
import sys
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, f1_score
import joblib


def train(df_input=None):
    # Load dataset
    if df_input is None:
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "profiles.csv")
        df = pd.read_csv(data_path)
    else:
        df = df_input
        
    print(f"[DATA] Loaded {len(df)} profiles for text training")

    # Handle empty/NaN bios
    df["bio"] = df["bio"].fillna("").astype(str)

    # TF-IDF vectorization
    print("[FEATURES] Vectorizing bios with TF-IDF...")
    vectorizer = TfidfVectorizer(
        max_features=1000,
        ngram_range=(1, 2),  # Unigrams + bigrams
        stop_words="english",
        min_df=2,
    )

    X_text = vectorizer.fit_transform(df["bio"])
    y = df["is_fake"]

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_text, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"   Train: {X_train.shape[0]}, Test: {X_test.shape[0]}")
    print(f"   Vocabulary size: {len(vectorizer.vocabulary_)}")

    # Cross-validation
    print("[SEARCH] Cross-validating...")
    model = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="f1")
    print(f"   CV F1 scores: {cv_scores}")
    print(f"   Mean CV F1: {cv_scores.mean():.4f}")

    # Final training
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    print(f"\n[METRICS] Accuracy: {accuracy:.4f}")
    print("\n[REPORT] Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Real", "Fake"]))

    # Top features
    feature_names = vectorizer.get_feature_names_out()
    coefs = model.coef_[0]
    top_fake = sorted(zip(feature_names, coefs), key=lambda x: x[1], reverse=True)[:10]
    top_real = sorted(zip(feature_names, coefs), key=lambda x: x[1])[:10]
    
    print("[FAKE WORDS] Top words indicating FAKE:")
    for word, coef in top_fake[:5]:
        print(f"   {word}: {coef:.4f}")
    
    print("[REAL WORDS] Top words indicating REAL:")
    for word, coef in top_real[:5]:
        print(f"   {word}: {coef:.4f}")

    # Save
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(models_dir, exist_ok=True)

    joblib.dump(model, os.path.join(models_dir, "text_model.pkl"))
    joblib.dump(vectorizer, os.path.join(models_dir, "vectorizer.pkl"))
    print(f"\n[SAVE] Models saved -> {models_dir}/")

    return {
        "accuracy": float(accuracy),
        "f1_score": float(f1),
        "vocab_size": int(len(vectorizer.vocabulary_)),
        "top_fake_words": [[word, float(coef)] for word, coef in top_fake[:10]],
        "top_real_words": [[word, float(coef)] for word, coef in top_real[:10]]
    }


if __name__ == "__main__":
    train()
