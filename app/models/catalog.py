from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, RootModel, model_validator


class CatalogEntry(BaseModel):
    """Schema for a single SHL assessment catalog entry."""

    model_config = ConfigDict(extra="ignore")

    entity_id: str
    name: str
    link: HttpUrl
    description: str
    duration: str | None = None
    job_levels: list[str] = Field(default_factory=list)
    keys: list[str] = Field(default_factory=list)
    job_families: list[str] = Field(default_factory=list)
    competencies: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    primary_function: str | None = None
    languages: list[str] = Field(default_factory=list)
    remote: str | None = None
    adaptive: str | None = None
    additional_data: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def populate_extra_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # If languages, remote, adaptive are in additional_data (for test compatibility)
            add_data = data.get("additional_data")
            if isinstance(add_data, dict):
                if "languages" in add_data and "languages" not in data:
                    data["languages"] = add_data["languages"]
                if "remote" in add_data and "remote" not in data:
                    data["remote"] = add_data["remote"]
                if "adaptive" in add_data and "adaptive" not in data:
                    data["adaptive"] = add_data["adaptive"]
        return data


class CatalogSchema(RootModel):
    """Root schema for validating the full catalog JSON."""

    root: list[CatalogEntry]
