"""Spam-detection REST API.

Endpoints required by the assignment:
  POST /predict  -> {"text": "..."}  returns {"label": "spam"|"ham"}
  GET  /healthz  -> 200 once the model is loaded

The model is loaded once at startup rather than per request, so /healthz only
returns 200 after the joblib bundle is in memory. That is what makes it usable
as a Kubernetes readiness probe in Question 4.
"""

import os

import joblib
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

MODEL_PATH = os.environ.get("MODEL_PATH", "model.joblib")
VERSION = os.environ.get("APP_VERSION", "v1")

app = FastAPI(title="Spam Detection API", version=VERSION)

model = None


class PredictRequest(BaseModel):
    text: str


@app.on_event("startup")
def load_model():
    global model
    model = joblib.load(MODEL_PATH)
    print(f"Model loaded from {MODEL_PATH}")


@app.get("/healthz")
def healthz():
    if model is None:
        return JSONResponse(status_code=503, content={"status": "loading"})
    return {"status": "ok", "version": VERSION}


@app.post("/predict")
def predict(request: PredictRequest):
    label = model.predict([request.text])[0]
    return {"label": label}
