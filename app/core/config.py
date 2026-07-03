from pathlib import Path

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    catalog_path: Path = Field(default=Path("./data/shl_assessments.json"))
    max_recommendations: int = Field(default=6)
    ranking_role_weight: float = Field(default=0.35)
    ranking_skills_weight: float = Field(default=0.40)
    ranking_competencies_weight: float = Field(default=0.10)
    ranking_seniority_weight: float = Field(default=0.10)
    ranking_duration_weight: float = Field(default=0.05)
    ranking_remote_weight: float = Field(default=0.00)
    llm_provider: str = Field(default="mock")
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")
    grok_api_key: str | None = Field(default=None)
    grok_model: str = Field(default="grok-4")
    grok_base_url: str = Field(default="https://api.x.ai/v1")
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")


settings = Settings()
