"""
Unified prediction engine.
Loads all models (XGBoost, Bio NLP, and Isolation Forest) and produces a combined risk score.
"""

import os
import logging
import joblib
import numpy as np
import pandas as pd
from src.features import extract_features, FEATURE_NAMES, SPAM_KEYWORDS

logger = logging.getLogger(__name__)

# --- Load models ---
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

tabular_model = None
text_model = None
vectorizer = None
anomaly_model = None


def load_models():
    """Load all models from disk."""
    global tabular_model, text_model, vectorizer, anomaly_model

    tabular_path = os.path.join(MODELS_DIR, "tabular_model.pkl")
    text_path = os.path.join(MODELS_DIR, "text_model.pkl")
    vec_path = os.path.join(MODELS_DIR, "vectorizer.pkl")
    anomaly_path = os.path.join(MODELS_DIR, "anomaly_model.pkl")

    if os.path.exists(tabular_path):
        try:
            tabular_model = joblib.load(tabular_path)
            logger.info("[OK] Tabular model loaded")
        except Exception as e:
            logger.error(f"Failed to load tabular model: {e}")
    else:
        logger.warning("Tabular model not found -- run train_tabular.py first")

    if os.path.exists(text_path) and os.path.exists(vec_path):
        try:
            text_model = joblib.load(text_path)
            vectorizer = joblib.load(vec_path)
            logger.info("[OK] Text NLP model loaded")
        except Exception as e:
            logger.error(f"Failed to load text NLP model: {e}")
    else:
        logger.warning("Text model not found -- run train_text.py first")

    if os.path.exists(anomaly_path):
        try:
            anomaly_model = joblib.load(anomaly_path)
            logger.info("[OK] Unsupervised anomaly model loaded")
        except Exception as e:
            logger.error(f"Failed to load anomaly model: {e}")
    else:
        logger.warning("Anomaly model not found -- run train_tabular.py first")


def generate_explanation(features, tab_score, text_score, anomaly_prob, final_score):
    """Generate a human-readable explanation of why a profile was flagged."""
    reasons = []
    
    # High risk
    if final_score > 0.7:
        risk_level = "High"
    elif final_score > 0.4:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # Check specific signals
    if features.get("followers_following_ratio", 1) < 0.05:
        reasons.append("Follows many more accounts than followers (suspicious ratio)")
    
    if features.get("bio_spam_keyword_count", 0) >= 3:
        reasons.append("Bio contains multiple spam keywords")
    
    if features.get("bio_is_empty", 0) == 1:
        reasons.append("Bio is empty")
    
    if features.get("very_new_account", 0) == 1:
        reasons.append("Account is very new (less than 30 days)")
    
    if features.get("zero_posts", 0) == 1:
        reasons.append("Account has zero posts")
    
    if features.get("username_digit_ratio", 0) > 0.4:
        reasons.append("Username contains excessive numbers")
        
    if features.get("username_consecutive_digits", 0) >= 4:
        reasons.append("Username contains suspicious run of digits")
    
    if features.get("username_length", 0) > 15:
        reasons.append("Username is unusually long")
    
    if features.get("has_profile_pic", 1) == 0:
        reasons.append("No profile picture")
    
    if features.get("following_much_more_than_followers", 0) == 1:
        reasons.append("Following count is disproportionately high")
    
    if features.get("bio_exclamation_count", 0) >= 3:
        reasons.append("Bio uses excessive exclamation marks")
        
    if features.get("bio_sentiment_score", 0.0) < -0.3:
        reasons.append("Bio sentiment analysis flagged spam/promotional tone")
        
    if features.get("bio_link_count", 0) >= 2:
        reasons.append("Bio contains multiple links or domain names")
    
    if features.get("high_follow_count", 0) == 1 and features.get("followers", 0) < 50:
        reasons.append("High following count but very few followers")

    if anomaly_prob > 0.65:
        reasons.append("Metadata distribution flags account as a structural outlier (Isolation Forest)")

    if not reasons:
        if final_score > 0.5:
            reasons.append("Combination of profile signals suggests suspicious activity")
        else:
            reasons.append("Profile appears to be legitimate")

    return {
        "risk_level": risk_level,
        "reasons": reasons,
    }


def predict_profile(profile):
    """
    Run all models on a profile and return a combined prediction.
    
    Args:
        profile: dict with username, bio, followers, following, posts, 
                 account_age_days (or age_days), has_profile_pic, has_url
    
    Returns:
        dict with prediction results
    """
    # Ensure models are loaded
    if tabular_model is None:
        load_models()

    # Extract features
    features = extract_features(profile)
    feature_vector = [features[name] for name in FEATURE_NAMES]

    # Sanitize features for JSON serialization (convert numpy types to Python native)
    features_clean = {
        k: (int(v) if isinstance(v, (int, bool)) else float(v))
        for k, v in features.items()
    }

    results = {
        "model_scores": {},
        "features_used": features_clean,
    }

    # --- 1. Tabular XGBoost Model ---
    tab_score = 0.5
    if tabular_model is not None:
        tab_proba = tabular_model.predict_proba([feature_vector])[0]
        tab_score = float(tab_proba[1])  # probability of fake
        results["model_scores"]["tabular"] = round(tab_score, 4)

    # --- 2. Text NLP Model ---
    text_score = 0.5
    if text_model is not None and vectorizer is not None:
        bio = str(profile.get("bio", ""))
        text_vec = vectorizer.transform([bio])
        text_proba = text_model.predict_proba(text_vec)[0]
        text_score = float(text_proba[1])  # probability of fake
        results["model_scores"]["text_nlp"] = round(text_score, 4)

    # --- 3. Unsupervised Anomaly Isolation Forest Model ---
    anomaly_prob = 0.5
    if anomaly_model is not None:
        # Use DataFrame with feature names to match training data and suppress warnings
        feature_df = pd.DataFrame([feature_vector], columns=FEATURE_NAMES)
        raw_anomaly_score = float(anomaly_model.score_samples(feature_df)[0])
        # score_samples returns negative values (closer to -1 is anomalous, closer to 0 is normal).
        # We scale it: -0.45 to -0.75 mapped to [0.0, 1.0]
        anomaly_prob = float(min(max((-raw_anomaly_score - 0.45) / 0.25, 0.0), 1.0))
        results["model_scores"]["anomaly"] = round(anomaly_prob, 4)

    # --- Weighted Score Fusion ---
    if anomaly_model is not None:
        TABULAR_WEIGHT = 0.50
        TEXT_WEIGHT = 0.30
        ANOMALY_WEIGHT = 0.20
        final_score = (TABULAR_WEIGHT * tab_score) + (TEXT_WEIGHT * text_score) + (ANOMALY_WEIGHT * anomaly_prob)
    else:
        TABULAR_WEIGHT = 0.65
        TEXT_WEIGHT = 0.35
        final_score = (TABULAR_WEIGHT * tab_score) + (TEXT_WEIGHT * text_score)
        
    final_score = round(min(max(final_score, 0.0), 1.0), 4)

    # --- Explanation ---
    explanation = generate_explanation(features, tab_score, text_score, anomaly_prob, final_score)

    results.update({
        "fake_probability": float(final_score),
        "fake_percentage": float(round(final_score * 100, 1)),
        "is_fake": bool(final_score > 0.5),
        "prediction": "FAKE" if final_score > 0.5 else "REAL",
        "risk_level": explanation["risk_level"],
        "reasons": [str(r) for r in explanation["reasons"]],
    })

    # Deep-sanitize: ensure all model_scores are Python floats
    results["model_scores"] = {
        k: float(v) for k, v in results["model_scores"].items()
    }

    return results


# Load models on import
load_models()
