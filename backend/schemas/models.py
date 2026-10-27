from pydantic import BaseModel, Field, field_validator
from enum import Enum
import uuid
from datetime import datetime

class ModelName(str, Enum):
    T5 = "t5"
    BART = "bart"
    PEGASUS = "pegasus"
    LLM = "llm"

class SummarizationRequest(BaseModel):
    article_text: str = Field(..., min_length=50, description="The news article to summarize")
    models: list[str] = Field(default=["t5", "bart", "pegasus", "llm"], description="Models to use")
    max_length: int = Field(default=150, ge=30, le=500)
    min_length: int = Field(default=30, ge=10, le=200)
    num_beams: int = Field(default=4, ge=1, le=10)
    reference_summary: str | None = Field(default=None, description="Optional reference for ROUGE")

    @field_validator("models")
    @classmethod
    def validate_models(cls, v: list[str]) -> list[str]:
        valid = {m.value for m in ModelName}
        for model in v:
            if model not in valid:
                raise ValueError(f"Invalid model '{model}'. Valid: {valid}")
        if not v:
            raise ValueError("At least one model must be selected")
        return v

    @field_validator("min_length")
    @classmethod
    def min_less_than_max(cls, v, info):
        # Note: info.data contains already-validated fields
        max_len = info.data.get("max_length", 150)
        if v >= max_len:
            raise ValueError("min_length must be less than max_length")
        return v

class ExperimentRequest(BaseModel):
    dataset: str = Field(default="cnn_dailymail", pattern="^(cnn_dailymail|xsum)$")
    num_samples: int = Field(default=5, ge=1, le=100)
    models: list[str] = Field(default=["t5", "bart", "pegasus"])
    include_llm: bool = Field(default=False, description="Include LLM (uses API calls)")
    max_length: int = Field(default=150, ge=30, le=500)
    min_length: int = Field(default=30, ge=10, le=200)

class EvaluationRequest(BaseModel):
    summary: str = Field(..., min_length=1)
    reference_summary: str = Field(..., min_length=1)
    model_name: str | None = None

class QualitativeScoreInput(BaseModel):
    model: str
    coherence: int = Field(..., ge=1, le=5)
    readability: int = Field(..., ge=1, le=5)
    factual_consistency: int = Field(..., ge=1, le=5)
    semantic_relevance: int = Field(..., ge=1, le=5)
    notes: str | None = None

# --- Response Models ---

class ArticleStats(BaseModel):
    char_count: int
    word_count: int
    sentence_count: int
    estimated_tokens: int

class PreprocessingInfo(BaseModel):
    original_length: int
    cleaned_length: int
    was_chunked: bool
    num_chunks: int
    cleaning_steps: list[str]

class SummaryResult(BaseModel):
    model: str
    summary: str | None = None
    word_count: int | None = None
    compression_ratio: float | None = None
    generation_time_seconds: float | None = None
    status: str  # "success", "error", "skipped"
    error: str | None = None

class RougeScores(BaseModel):
    rouge_1: float
    rouge_2: float
    rouge_l: float

class QualitativeScore(BaseModel):
    coherence: int = Field(..., ge=1, le=5)
    readability: int = Field(..., ge=1, le=5)
    factual_consistency: int = Field(..., ge=1, le=5)
    semantic_relevance: int = Field(..., ge=1, le=5)
    notes: str | None = None

class EvaluationResult(BaseModel):
    model: str
    rouge: RougeScores | None = None
    qualitative: QualitativeScore | None = None
    message: str | None = None

class ComparisonResult(BaseModel):
    rankings: list[dict]
    best_model: str | None = None
    analysis: str

class SummarizationResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    article_stats: ArticleStats
    preprocessing_info: PreprocessingInfo
    summaries: list[SummaryResult]
    evaluation: list[EvaluationResult] | None = None
    comparison: ComparisonResult | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EvaluationResponse(BaseModel):
    rouge: RougeScores
    model_name: str | None = None

class ModelInfo(BaseModel):
    name: str
    display_name: str
    checkpoint: str
    status: str  # "available", "loaded", "error", "unavailable"
    description: str
    max_input_tokens: int
    is_local: bool

class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    device: str
    loaded_models: list[str]
    available_models: list[str]
    groq_configured: bool

class ExperimentStatus(BaseModel):
    experiment_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: float  # 0.0 to 1.0
    current_step: str
    total_samples: int
    completed_samples: int
    errors: list[str]

class ExperimentResult(BaseModel):
    experiment_id: str
    dataset: str
    num_samples: int
    models: list[str]
    results: list[dict]
    aggregate_scores: dict
    timestamp: datetime
    execution_time_seconds: float
    device: str

class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    status_code: int
