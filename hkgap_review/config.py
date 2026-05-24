from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    llm_provider: str = Field(default="openai")
    model_name: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.1)
    max_tokens: int = Field(default=1500)
    request_timeout: float = Field(default=60.0)
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_version: str = "2024-08-01-preview"
    prompt_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent / "prompts")

    @classmethod
    def from_env(
        cls,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> Settings:
        return cls(
            llm_provider=(provider_override or os.getenv("LLM_PROVIDER", "openai")).strip(),
            model_name=(model_override or os.getenv("MODEL_NAME", "gpt-4o-mini")).strip(),
            temperature=float(os.getenv("TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("MAX_TOKENS", "1500")),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL"),
            azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        )
