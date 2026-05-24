from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from openai import AsyncAzureOpenAI, AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import Settings
from ..schemas import AgentReview, Paragraph


class LLMProvider(Protocol):
    async def generate_json(
        self, agent_name: str, system_prompt: str, user_prompt: str
    ) -> dict: ...


class OpenAIJSONProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

        provider = settings.llm_provider.lower()
        if provider == "azure_openai":
            if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
                raise ValueError("Azure OpenAI provider selected but endpoint/key are missing.")
            self.client = AsyncAzureOpenAI(
                api_key=settings.azure_openai_api_key,
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
            )
        else:
            api_key = settings.openai_api_key
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for non-mock providers.")
            self.client = AsyncOpenAI(api_key=api_key, base_url=settings.openai_base_url)

    async def generate_json(self, agent_name: str, system_prompt: str, user_prompt: str) -> dict:
        completion = await self.client.chat.completions.create(
            model=self.settings.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            timeout=self.settings.request_timeout,
        )
        message = completion.choices[0].message.content or "{}"
        return json.loads(message)


class MockLLMProvider:
    def __init__(self, canned_responses: dict[str, dict]):
        self.canned_responses = canned_responses

    async def generate_json(self, agent_name: str, system_prompt: str, user_prompt: str) -> dict:
        payload = self.canned_responses.get(agent_name)
        if payload is None:
            return {
                "agent": agent_name,
                "commentary": None,
                "referee_items": [],
                "checklist": [],
                "integrity_flags": [],
                "unsupported_claims": [],
            }
        return payload


class BaseAgent:
    agent_name: str = "BaseAgent"
    prompt_filename: str = ""

    def __init__(self, provider: LLMProvider, settings: Settings):
        self.provider = provider
        self.settings = settings
        self.system_prompt = self._load_prompt(settings.prompt_dir / self.prompt_filename)

    @staticmethod
    def _load_prompt(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _user_prompt(self, paragraph: Paragraph, context: str) -> str:
        return (
            "Return a JSON object matching the schema exactly.\n"
            f"Section: {paragraph.section}\n"
            f"Paragraph index: {paragraph.index}\n"
            f"Paragraph text:\n{paragraph.text}\n\n"
            f"Paper context:\n{context}"
        )

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    async def run(self, paragraph: Paragraph, context: str) -> AgentReview:
        payload = await self.provider.generate_json(
            agent_name=self.agent_name,
            system_prompt=self.system_prompt,
            user_prompt=self._user_prompt(paragraph, context),
        )
        payload.setdefault("agent", self.agent_name)
        return AgentReview.model_validate(payload)


def build_provider(
    settings: Settings, canned_responses: dict[str, dict] | None = None
) -> LLMProvider:
    if settings.llm_provider.lower() == "mock":
        return MockLLMProvider(canned_responses or {})
    return OpenAIJSONProvider(settings)
