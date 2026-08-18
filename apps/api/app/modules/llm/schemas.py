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
        provider = os.getenv("LLM_PROVIDER", "openai_compatible").strip()
        api_key = os.getenv("LLM_API_KEY", "").strip()
        model = os.getenv("LLM_MODEL", "").strip()
        base_url = os.getenv("LLM_BASE_URL", "").strip()
        if not api_key or not model or not base_url:
            raise LLMGatewayError(
                "LLM_API_KEY, LLM_MODEL, and LLM_BASE_URL are required in llm mode."
            )
        if provider != "openai_compatible":
            raise LLMGatewayError("Only the openai_compatible provider is supported by this MVP.")
        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url.rstrip("/"),
        )
