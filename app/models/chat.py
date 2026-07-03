from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: datetime | None = None


class ChatRequest(BaseModel):
    conversation: list[Message] = Field(..., min_length=1)
    session_id: str | None = None


class Recommendation(BaseModel):
    entity_id: str
    name: str
    link: HttpUrl
    description: str
    ranking_score: float = 0.0
    matched_criteria: list[str] = Field(default_factory=list)
    explanation: str = ""
    duration: str | None = None
    job_levels: list[str] = Field(default_factory=list)
    keys: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    recommendations: list[Recommendation]
    end_of_conversation: bool


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    message: str
