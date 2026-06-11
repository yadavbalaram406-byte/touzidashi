from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class EvaluationStatusResponse(BaseModel):
    id: int
    status: str
    final_score: Optional[float] = None
    decision: Optional[str] = None
    error_message: Optional[str] = None


class EvaluationListItem(BaseModel):
    id: int
    project_name: str
    original_filename: str
    file_type: str
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    final_score: Optional[float] = None
    decision: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationListResponse(BaseModel):
    items: list[EvaluationListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ScoreDimensionResult(BaseModel):
    key: str
    name: str
    max_score: int
    score: float
    tier_label: str
    reasoning: str


class EvaluationDetailResponse(BaseModel):
    id: int
    project_name: str
    original_filename: str
    file_type: str
    text_length: Optional[int] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    project_intro: Optional[dict] = None
    scores: Optional[list[ScoreDimensionResult]] = None
    score_team: Optional[float] = None
    score_pain_point: Optional[float] = None
    score_traction: Optional[float] = None
    score_moat: Optional[float] = None
    final_score: Optional[float] = None
    decision: Optional[str] = None
    suggestions: Optional[dict] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    id: int
    project_name: str
    status: str
    message: str


class ConfigResponse(BaseModel):
    llm_provider: str
    llm_model: str
    has_api_key: bool


class TestLLMResponse(BaseModel):
    success: bool
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None
