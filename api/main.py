from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import pandas as pd
from pathlib import Path
import joblib

app = FastAPI(
    title="Network Threat Detection API"
)

# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Path to the saved ML model
MODEL_PATH = BASE_DIR / "models" / "threat_detection_model.joblib"

# Load the trained model
model = joblib.load(MODEL_PATH)

class PredictionRequest(BaseModel):
    features: Dict[str, float]

@app.get("/")
def home():
    return {
        "message": "Network Threat Detection API is running!"
    }


@app.get("/model-info")
def model_info():
    return {
        "model": "Random Forest Classifier",
        "classes": list(model.classes_),
        "number_of_features": model.n_features_in_
    }

@app.post("/predict")
def predict(request: PredictionRequest):

    # Convert incoming features into a DataFrame
    input_data = pd.DataFrame([request.features])

    # Make sure all 78 required features are present
    expected_features = list(model.feature_names_in_)

    missing_features = [
        feature for feature in expected_features
        if feature not in input_data.columns
    ]

    if missing_features:
        raise HTTPException(
            status_code=400,
            detail=f"Missing features: {missing_features}"
        )

    # Put features in the exact order used during training
    input_data = input_data[expected_features]

    # Make prediction
    prediction = model.predict(input_data)[0]

    # Get prediction probabilities
    probabilities = model.predict_proba(input_data)[0]

    confidence = float(max(probabilities))

    # Determine threat status
    if prediction == "BENIGN":
        threat_status = "No Threat Detected"
        risk_level = "Low"

    else:
        threat_status = "Threat Detected"

        # Determine risk level based on model confidence
        if confidence >= 0.8:
            risk_level = "High"
        elif confidence >= 0.5:
            risk_level = "Medium"
        else:
            risk_level = "Low"

    return {
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "threat_status": threat_status,
        "risk_level": risk_level
    }