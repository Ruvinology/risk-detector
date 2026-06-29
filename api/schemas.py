from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="SMS, WhatsApp, email, or social message text to analyze.",
        examples=[
            "Your bank account has been blocked. Click this link immediately to verify your details"
        ],
    )


class MessageAnalysis(BaseModel):
    prediction: str
    risk_score: float
    risk_level: str
    probabilities: dict[str, float]


class ScamTypeAnalysis(BaseModel):
    scam_type: str
    confidence: float
    probabilities: dict[str, float]


class UrlAnalysisItem(BaseModel):
    url: str
    url_risk_score: int
    url_risk_factors: list[str]
    trusted: bool = False


class AnalysisMeta(BaseModel):
    models: str
    external_ai_apis: bool


class AnalyzeResponse(BaseModel):
    verdict: str
    delivery_action: Literal["allow", "warn", "block"]
    final_risk_score: float
    final_risk_level: Literal["High Risk", "Medium Risk", "Low Risk"]
    message_analysis: MessageAnalysis
    scam_type: ScamTypeAnalysis
    explanation: list[str]
    url_analysis: list[UrlAnalysisItem]
    safety_advice: list[str]
    meta: AnalysisMeta


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    models_loaded: bool
    service: str
    version: str


class FeedbackRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10_000)
    predicted_action: Literal["allow", "warn", "block"]
    predicted_verdict: str
    user_rating: Literal["correct", "wrong"]
    correct_label: Literal["safe", "suspicious", "scam"] | None = None
    source: str = "demo-client"


class FeedbackResponse(BaseModel):
    status: Literal["saved"]
    message: str
