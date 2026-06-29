import logging
import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
)
from src.service import analyze_message, warm_models
from src.feedback import save_feedback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scamshield.api")

APP_VERSION = "1.0.0"
_models_ready = False

app = FastAPI(
    title="ScamShield AI API",
    description=(
        "REST API for scam and spam message detection. "
        "Powered by locally trained ML models on a custom dataset — "
        "no external LLM APIs required."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_warm_models():
    global _models_ready
    try:
        warm_models()
        _models_ready = True
        logger.info("Models warmed up successfully.")
    except Exception as exc:
        _models_ready = False
        logger.error("Model warmup failed: %s", exc)


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    return HealthResponse(
        status="ok" if _models_ready else "degraded",
        models_loaded=_models_ready,
        service="ScamShield AI",
        version=APP_VERSION,
    )


@app.post("/v1/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
def analyze(request: AnalyzeRequest):
    if not _models_ready:
        raise HTTPException(
            status_code=503,
            detail="Models are not loaded yet. Try again in a moment.",
        )

    try:
        result = analyze_message(request.message)
        return AnalyzeResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Analysis failed")
        raise HTTPException(
            status_code=500,
            detail="Analysis failed due to an internal error.",
        ) from exc


@app.post("/v1/feedback", response_model=FeedbackResponse, tags=["Feedback"])
def submit_feedback(request: FeedbackRequest):
    if request.user_rating == "wrong" and not request.correct_label:
        raise HTTPException(
            status_code=400,
            detail="correct_label is required when user_rating is 'wrong'.",
        )

    save_feedback(
        message=request.message,
        predicted_action=request.predicted_action,
        predicted_verdict=request.predicted_verdict,
        user_rating=request.user_rating,
        correct_label=request.correct_label,
        source=request.source,
    )

    return FeedbackResponse(
        status="saved",
        message="Thank you — your feedback helps improve the model.",
    )
