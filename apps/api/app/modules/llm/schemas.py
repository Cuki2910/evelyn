from dataclasses import dataclass
import os


class LLMGatewayError(RuntimeError):
    """Raised when an LLM response cannot be safely used."""


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    api_key: str
    model: str
    base_url: str

    @classmethod
    def from_environment(cls) -> "LLMSettings":
        provider = os.getenv("LLM_PROVIDER", "openrouter").strip()
        api_key = os.getenv("LLM_API_KEY", "").strip()
        model = os.getenv("LLM_MODEL", "openai/gpt-5.4-mini").strip()
        base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1").strip()
        if not api_key:
            raise LLMGatewayError("LLM_API_KEY is required in llm mode.")
        if provider != "openrouter":
            raise LLMGatewayError("Only the openrouter provider is supported by this MVP.")
        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url.rstrip("/"),
        )
