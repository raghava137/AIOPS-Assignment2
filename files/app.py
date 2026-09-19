"""Spam-detection API with a Redis cache in front of the model.

Flow for POST /predict:
  1. look the exact input text up in Redis
  2. HIT  -> return the cached label, model never runs
     MISS -> run the model, write the label to Redis with a TTL, return it

The response carries "cached": true/false and "elapsed_ms" so a cache hit can
be shown to be measurably faster rather than merely asserted.

Redis is reached by its Compose service name, which is why REDIS_HOST defaults
to "cache": inside the Compose network that name resolves to the Redis
container.
"""

import hashlib
import os
import time

import joblib
import redis
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

MODEL_PATH = os.environ.get("MODEL_PATH", "model.joblib")
VERSION = os.environ.get("APP_VERSION", "v1")

REDIS_HOST = os.environ.get("REDIS_HOST", "cache")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
CACHE_TTL = int(os.environ.get("CACHE_TTL", "300"))

app = FastAPI(title="Spam Detection API", version=VERSION)

model = None
cache = None


class PredictRequest(BaseModel):
    text: str


def cache_key(text: str) -> str:
    """Hash the text so arbitrary message content is a safe Redis key."""
    return "spam:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@app.on_event("startup")
def startup():
    global model, cache
    model = joblib.load(MODEL_PATH)
    print(f"Model loaded from {MODEL_PATH}")

    cache = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT,
        decode_responses=True, socket_connect_timeout=2,
    )
    try:
        cache.ping()
        print(f"Redis reachable at {REDIS_HOST}:{REDIS_PORT}")
    except redis.exceptions.RedisError as err:
        # The API stays useful without the cache; it just recomputes every time.
        print(f"Redis unavailable ({err}); running without cache")
        cache = None


@app.get("/healthz")
def healthz():
    if model is None:
        return JSONResponse(status_code=503, content={"status": "loading"})
    return {"status": "ok", "version": VERSION}


@app.post("/predict")
def predict(request: PredictRequest):
    start = time.perf_counter()
    key = cache_key(request.text)

    if cache is not None:
        try:
            hit = cache.get(key)
            if hit is not None:
                elapsed = (time.perf_counter() - start) * 1000
                return {"label": hit, "cached": True,
                        "elapsed_ms": round(elapsed, 3)}
        except redis.exceptions.RedisError:
            pass

    label = model.predict([request.text])[0]

    if cache is not None:
        try:
            cache.setex(key, CACHE_TTL, label)
        except redis.exceptions.RedisError:
            pass

    elapsed = (time.perf_counter() - start) * 1000
    return {"label": label, "cached": False, "elapsed_ms": round(elapsed, 3)}
