"""
FastAPI backend for the Fake Profile Detection System.
Endpoints: auth, predict, stats, history, extension, batch, feedback, retrain.
Serves the React frontend in production mode.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add project root so imports work with `uvicorn src.api:app`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.auth import register_user, login_user, get_current_user, require_auth
from src.predict import predict_profile, load_models
from src.database import init_db, get_db

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


# --- Lifespan (startup/shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load ML models on startup to avoid cold-start latency."""
    logger.info("[START] Starting Fake Profile Detection API...")
    init_db()
    load_models()
    logger.info("[OK] All models loaded and ready")
    yield
    logger.info("[SHUTDOWN] Shutting down API")


# --- App ---
app = FastAPI(
    title="Fake Profile Detection API",
    description="AI-powered system to detect fake social media profiles",
    version="1.1.0",
    lifespan=lifespan,
)

# --- CORS (allow frontend & extension) ---
ALLOWED_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Models ---
class UserAuth(BaseModel):
    username: str
    password: str


class ProfileInput(BaseModel):
    username: str
    bio: str = ""
    followers: int = 0
    following: int = 0
    posts: int = 0
    account_age_days: int = 1
    has_profile_pic: int = 1
    has_url: int = 0


class BatchInput(BaseModel):
    profiles: List[ProfileInput]


class FeedbackInput(BaseModel):
    username: str
    bio: str = ""
    followers: int = 0
    following: int = 0
    posts: int = 0
    account_age_days: int = 1
    has_profile_pic: int = 1
    has_url: int = 0
    is_fake: int  # 0 for Real, 1 for Fake


# --- Helper ---
def _run_prediction(profile: ProfileInput, requesting_user: str = None) -> dict:
    """Run prediction and track analytics."""
    profile_data = profile.model_dump() if hasattr(profile, 'model_dump') else profile.dict()
    result = predict_profile(profile_data)

    # Save to history database
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO history 
               (requesting_user, target_username, prediction, fake_probability, risk_level, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (
                requesting_user,
                profile.username,
                result["prediction"],
                result["fake_probability"],
                result["risk_level"],
                datetime.now(timezone.utc).isoformat()
            )
        )
        
        if requesting_user:
            cursor.execute(
                "UPDATE users SET predictions_count = predictions_count + 1 WHERE username = ?",
                (requesting_user,)
            )
        conn.commit()

    return result


# =============================================
#  ROUTES
# =============================================

@app.get("/")
def root():
    return {
        "message": "🛡️ Fake Profile Detection API",
        "version": "1.1.0",
        "docs": "/docs",
    }


# --- Auth ---
@app.post("/register")
def register(user: UserAuth):
    """Register a new user."""
    result = register_user(user.username, user.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    logger.info(f"New user registered: {user.username}")
    return result


@app.post("/login")
def login(user: UserAuth):
    """Login and receive a JWT token."""
    result = login_user(user.username, user.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    logger.info(f"User logged in: {user.username}")
    return result


# --- Predictions (optional auth — tracks user if token provided) ---
@app.post("/predict")
def predict(
    profile: ProfileInput,
    current_user: Optional[str] = Depends(get_current_user),
):
    """Analyze a profile and return fake detection results."""
    user_label = f"@{current_user}" if current_user else "anonymous"
    logger.info(f"Prediction requested by {user_label} for: @{profile.username}")

    try:
        result = _run_prediction(profile, current_user)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    logger.info(
        f"Result: {result['prediction']} "
        f"(probability: {result['fake_percentage']}%, "
        f"risk: {result['risk_level']})"
    )
    return result


@app.post("/predict/batch")
def predict_batch(
    batch: BatchInput,
    current_user: Optional[str] = Depends(get_current_user),
):
    """Analyze multiple profiles at once. Max 50 per request."""
    if len(batch.profiles) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 profiles per batch request")

    results = []
    for profile in batch.profiles:
        try:
            result = _run_prediction(profile, current_user)
            results.append({"username": profile.username, **result})
        except Exception as e:
            results.append({"username": profile.username, "error": str(e)})

    return {
        "total": len(results),
        "results": results,
        "fake_count": sum(1 for r in results if r.get("is_fake")),
        "real_count": sum(1 for r in results if r.get("is_fake") is False),
    }


# --- Extension endpoint (no auth, for Chrome extension) ---
@app.post("/api/extension/predict")
def extension_predict(profile: ProfileInput):
    """Public endpoint for Chrome extension — no auth required."""
    logger.info(f"Extension prediction for: @{profile.username}")
    try:
        result = _run_prediction(profile, "extension")
    except Exception as e:
        logger.error(f"Extension prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    return result


# --- Analytics ---
@app.get("/stats")
def get_stats(current_user: Optional[str] = Depends(get_current_user)):
    """Get detection statistics."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM history")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM history WHERE prediction = 'FAKE'")
        fake = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM history WHERE prediction = 'REAL'")
        real = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM feedback_profiles")
        feedback_count = cursor.fetchone()[0]
        
    return {
        "summary": {"total": total, "fake": fake, "real": real, "feedback": feedback_count},
        "chart_data": [
            {"name": "Fake", "count": fake, "color": "#ef4444"},
            {"name": "Real", "count": real, "color": "#22c55e"},
        ],
        "total_predictions": total,
    }


@app.get("/history")
def get_history(
    limit: int = 50,
    current_user: Optional[str] = Depends(get_current_user),
):
    """Get recent prediction history."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM history")
        total = cursor.fetchone()[0]
        
        cursor.execute(
            "SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", 
            (limit,)
        )
        rows = cursor.fetchall()
        
    # Convert rows to dict
    history_list = []
    for row in rows:
        history_list.append({
            "id": row["id"],
            "requesting_user": row["requesting_user"],
            "username": row["target_username"],
            "prediction": row["prediction"],
            "fake_probability": row["fake_probability"],
            "risk_level": row["risk_level"],
            "timestamp": row["timestamp"]
        })
        
    return {
        "predictions": history_list,
        "total": total,
    }


# --- Human-in-the-loop AI Endpoints ---

@app.post("/feedback")
def submit_feedback(
    feedback: FeedbackInput,
    current_user: str = Depends(require_auth)
):
    """Submit profile override correction to database (user authenticated)."""
    logger.info(f"Feedback submitted by {current_user} for @{feedback.username} -> is_fake={feedback.is_fake}")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO feedback_profiles 
               (username, bio, followers, following, posts, account_age_days, has_profile_pic, has_url, is_fake, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                feedback.username,
                feedback.bio,
                feedback.followers,
                feedback.following,
                feedback.posts,
                feedback.account_age_days,
                feedback.has_profile_pic,
                feedback.has_url,
                feedback.is_fake,
                datetime.now(timezone.utc).isoformat()
            )
        )
        conn.commit()
        
    return {"success": True, "message": "Feedback submitted successfully"}


@app.post("/retrain")
def retrain_models(
    current_user: str = Depends(require_auth)
):
    """Trigger retraining of all models incorporating feedback data (user authenticated)."""
    logger.info(f"[RETRAIN] Retraining triggered by admin user: {current_user}")
    
    import pandas as pd
    from src.train_tabular import train as train_tabular
    from src.train_text import train as train_text
    
    try:
        # Load base synthetic dataset
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "profiles.csv")
        df_base = pd.read_csv(data_path)
        
        # Load custom feedback profiles from SQLite
        with get_db() as conn:
            query = "SELECT username, bio, followers, following, posts, account_age_days, has_profile_pic, has_url, is_fake FROM feedback_profiles"
            df_feedback = pd.read_sql_query(query, conn)
            
        logger.info(f"Loaded {len(df_base)} base profiles and {len(df_feedback)} user-submitted feedback profiles.")
        
        # Merge datasets
        if not df_feedback.empty:
            df_combined = pd.concat([df_base, df_feedback], ignore_index=True)
            logger.info(f"Combined dataset has {len(df_combined)} samples.")
        else:
            df_combined = df_base
            logger.info("No feedback samples found. Using base profiles only.")
            
        # Retrain text NLP model
        logger.info("Retraining NLP Bio Model...")
        text_metrics = train_text(df_combined)
        
        # Retrain tabular XGBoost + Unsupervised Isolation Forest
        logger.info("Retraining Tabular XGBoost & Anomaly Isolation Forest...")
        tabular_metrics = train_tabular(df_combined)
        
        # Reload models in memory
        logger.info("Reloading newly trained models...")
        load_models()
        
        return {
            "success": True,
            "message": "Models retrained and reloaded successfully!",
            "samples_trained": len(df_combined),
            "feedback_samples": len(df_feedback),
            "nlp_metrics": text_metrics,
            "tabular_metrics": tabular_metrics
        }
    except Exception as e:
        logger.error(f"Failed to retrain models: {e}")
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# --- Serve frontend static files (production) ---
FRONTEND_BUILD = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend", "dist"
)

if os.path.isdir(FRONTEND_BUILD):
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_BUILD, "assets")), name="static")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the React SPA for any non-API routes."""
        file_path = os.path.join(FRONTEND_BUILD, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_BUILD, "index.html"))
