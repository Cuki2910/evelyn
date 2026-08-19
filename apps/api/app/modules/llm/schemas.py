from dataclasses import dataclass
import os


class LLMGatewayError(RuntimeError):
    """Raised when an LLM response cannot be safely used."""


class RetryableLLMGatewayError(LLMGatewayError):
    """A quota or transport failure that may safely use another configured provider."""


# provider -> (default model, default base URL)
PROVIDER_DEFAULTS: dict[str, tuple[str, str]] = {
    "openrouter": ("openai/gpt-5.4-mini", "https://openrouter.ai/api/v1"),
    "groq": ("openai/gpt-oss-120b", "https://api.groq.com/openai/v1"),
    "gemini": ("gemini-3.6-flash", "https://generativelanguage.googleapis.com/v1beta/openai"),
}


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    api_key: str
    model: str
    base_url: str

    @classmethod
    def from_environment(cls) -> "LLMSettings":
        provider = os.getenv("LLM_PROVIDER", "openrouter").strip()
        if provider not in PROVIDER_DEFAULTS:
            raise LLMGatewayError(
                f"Unsupported LLM_PROVIDER '{provider}'. Supported providers: "
                f"{', '.join(sorted(PROVIDER_DEFAULTS))}."
            )
        default_model, default_base_url = PROVIDER_DEFAULTS[provider]
        api_key = os.getenv("LLM_API_KEY", "").strip()
        model = os.getenv("LLM_MODEL", "").strip() or default_model
        base_url = (os.getenv("LLM_BASE_URL", "").strip() or default_base_url).rstrip("/")
        if not api_key:
            raise LLMGatewayError("LLM_API_KEY is required in llm mode.")
        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
        )

    @classmethod
    def fallback_settings_from_environment(cls) -> list["LLMSettings"]:
        """Return explicitly configured secondary providers in deterministic order."""

        if os.getenv("LLM_FALLBACK_ENABLED", "false").strip().casefold() != "true":
            return []

        primary = os.getenv("LLM_PROVIDER", "openrouter").strip()
        fallbacks: list[LLMSettings] = []
        for provider, prefix in (("gemini", "GEMINI"), ("groq", "GROQ"), ("openrouter", "OPENROUTER")):
            if provider == primary:
                continue
            api_key = os.getenv(f"{prefix}_API_KEY", "").strip()
            if not api_key:
                continue
            default_model, default_base_url = PROVIDER_DEFAULTS[provider]
            fallbacks.append(
                cls(
                    provider=provider,
                    api_key=api_key,
                    model=os.getenv(f"{prefix}_MODEL", "").strip() or default_model,
                    base_url=(os.getenv(f"{prefix}_BASE_URL", "").strip() or default_base_url).rstrip("/"),
                )
            )
        return fallbacks
