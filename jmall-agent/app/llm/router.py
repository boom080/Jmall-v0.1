"""LLM Router that classifies task complexity and routes to appropriate models."""

import logging
from typing import Dict, Optional, Tuple

from app.core.config import Settings

logger = logging.getLogger(__name__)

# Task complexity classification: maps agent_type to cost tier
# cheap  -> simple tasks (search, rule-based checks)
# medium -> evaluation, rewriting
# strong -> creative writing, planning, orchestration
TASK_COMPLEXITY: Dict[str, str] = {
    "market_research": "cheap",       # simple search + summarize
    "keyword_extraction": "cheap",
    "compliance_check": "cheap",      # rule-based + simple LLM
    "compliance_review": "cheap",     # rule-based + simple LLM
    "copy_generation": "strong",      # creative writing
    "style_adaptation": "medium",     # rewriting
    "orchestration": "cheap",         # simple planning — use fast/cheap model
    "review_quality": "medium",       # evaluation
}

# Model selection per tier per provider
TIER_MODEL_DEFAULTS: Dict[str, Dict[str, str]] = {
    "mock": {
        "cheap": "mock-product-copy-v1",
        "medium": "mock-product-copy-v1",
        "strong": "mock-product-copy-v1",
    },
    "deepseek": {
        "cheap": "deepseek-chat",
        "medium": "deepseek-chat",
        "strong": "deepseek-chat",
    },
    "qwen": {
        "cheap": "qwen-turbo",
        "medium": "qwen-plus",
        "strong": "qwen-max",
    },
}

# Estimated token costs for budget estimation (per 1K tokens)
ESTIMATED_COST_PER_1K: Dict[str, float] = {
    "cheap": 0.0005,
    "medium": 0.002,
    "strong": 0.01,
}


class LLMRouter:
    """Routes tasks to appropriate models based on complexity and cost.

    Usage:
        router = LLMRouter(settings, provider_factory)
        provider, model = router.route("copy_generation")
    """

    TASK_COMPLEXITY = TASK_COMPLEXITY

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._provider_cache: Dict[str, str] = {}

    def _validate_provider(self, provider_name: str) -> str | None:
        """Validate that a provider has its API key configured. Returns provider name or None."""
        name = (provider_name or "").strip().lower()
        if name == "mock":
            return "mock"
        if name == "deepseek" and self.settings.deepseek_api_key.strip():
            return "deepseek"
        if name == "qwen" and self.settings.qwen_api_key.strip():
            return "qwen"
        return None

    def _resolve_provider(self) -> str:
        """Determine the best available provider for agent tasks."""
        # Prefer configured agent provider, fall back to main ai_provider, then mock
        configured = (self.settings.agent_default_provider or "").strip().lower()
        validated = self._validate_provider(configured)
        if validated:
            return validated

        # Fall back to main AI provider
        main_provider = (self.settings.ai_provider or "mock").strip().lower()
        validated = self._validate_provider(main_provider)
        if validated:
            return validated

        # If nothing is configured, return mock
        if not self.settings.deepseek_api_key.strip() and not self.settings.qwen_api_key.strip():
            return "mock"

        # Prefer the first available real provider
        if self.settings.deepseek_api_key.strip():
            return "deepseek"
        if self.settings.qwen_api_key.strip():
            return "qwen"
        return "mock"

    def _resolve_provider_for_tier(self, tier: str) -> str:
        """Determine which provider to use for a given cost tier.

        Checks tier-specific overrides first (AGENT_STRONG_PROVIDER etc.),
        then falls back to the global provider resolution.
        """
        tier_provider_map = {
            "strong": self.settings.agent_strong_provider,
            "medium": self.settings.agent_medium_provider,
            "cheap": self.settings.agent_cheap_provider,
        }
        tier_provider = (tier_provider_map.get(tier, "") or "").strip().lower()
        validated = self._validate_provider(tier_provider)
        if validated:
            logger.debug("LLM Router: tier=%s -> provider=%s (tier override)", tier, validated)
            return validated

        # Fall back to global resolution
        return self._resolve_provider()

    def _resolve_model_for_tier(self, provider: str, tier: str) -> str:
        """Determine which model to use for a given provider + tier.

        Checks tier-specific model overrides first, then falls back to
        provider defaults in TIER_MODEL_DEFAULTS.
        """
        tier_model_map = {
            "strong": self.settings.agent_strong_model,
            "medium": self.settings.agent_medium_model,
            "cheap": self.settings.agent_cheap_model,
        }
        tier_model = (tier_model_map.get(tier, "") or "").strip()
        if tier_model:
            return tier_model

        # Fall back to provider-tier defaults
        return TIER_MODEL_DEFAULTS.get(provider, {}).get(tier, "mock-product-copy-v1")

    def route(self, agent_type: str) -> Tuple[str, str]:
        """Route an agent type to (provider_name, model_name).

        Routing priority per tier:
        1. AGENT_{STRONG,MEDIUM,CHEAP}_PROVIDER  — tier-specific provider
        2. AGENT_DEFAULT_PROVIDER / AI_PROVIDER  — global fallback
        3. Auto-detect from available API keys

        Model selection per tier:
        1. AGENT_{STRONG,MEDIUM,CHEAP}_MODEL     — tier-specific model
        2. TIER_MODEL_DEFAULTS[provider][tier]   — provider defaults

        Returns:
            Tuple of (provider_name, model_name)
        """
        tier = TASK_COMPLEXITY.get(agent_type, "medium")
        provider = self._resolve_provider_for_tier(tier)
        model = self._resolve_model_for_tier(provider, tier)

        logger.info("LLM Router: agent=%s tier=%s -> provider=%s model=%s", agent_type, tier, provider, model)
        return provider, model

    def estimate_cost(self, agent_type: str, input_tokens: int, output_tokens: int = 0) -> float:
        """Estimate the cost for a task based on agent type and token counts.

        Args:
            agent_type: The type of agent task
            input_tokens: Estimated input tokens
            output_tokens: Estimated output tokens (default 0, will use input * 0.5)

        Returns:
            Estimated cost in USD
        """
        tier = TASK_COMPLEXITY.get(agent_type, "medium")
        cost_per_1k = ESTIMATED_COST_PER_1K.get(tier, 0.002)
        if output_tokens <= 0:
            output_tokens = max(int(input_tokens * 0.5), 50)
        total_tokens = input_tokens + output_tokens
        estimated = (total_tokens / 1000) * cost_per_1k
        return round(estimated, 6)

    def get_tier_for_agent(self, agent_type: str) -> str:
        """Get the complexity tier for an agent type."""
        return TASK_COMPLEXITY.get(agent_type, "medium")

    def get_available_models_for_tier(self, tier: str) -> Dict[str, str]:
        """List available models for a given cost tier."""
        provider = self._resolve_provider()
        if provider in TIER_MODEL_DEFAULTS:
            return {provider: TIER_MODEL_DEFAULTS[provider].get(tier, "unknown")}
        return {}
