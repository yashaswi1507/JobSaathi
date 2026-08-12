#!/bin/bash
# CareerShield AI — Production Startup Script

echo "CareerShield AI Starting..."

# Check ML models
if [ -f "/app/ml_models/xgboost_fraud_model.pkl" ]; then
    echo "ML models found — Full fraud detection active"
else
    echo "ML models missing — Rule-based fallback will be used"
fi

# Start FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
