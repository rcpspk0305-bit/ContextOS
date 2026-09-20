from typing import Dict, Tuple

# Pricing per million tokens: (prompt_price_per_m, completion_price_per_m)
MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    # Anthropic
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "claude-3-haiku": (0.25, 1.25),
    "claude-3-haiku-20240307": (0.25, 1.25),
    "claude-3-opus": (15.00, 75.00),
    "claude-3-opus-20240229": (15.00, 75.00),

    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "o1": (15.00, 60.00),
    "o1-preview": (15.00, 60.00),
    "o1-mini": (3.00, 12.00),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),

    # Google
    "gemini-1.5-pro": (1.25, 5.00),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-ultra": (2.50, 10.00),

    # Local / Open Source (Free compute cost for tokens)
    "llama3": (0.0, 0.0),
    "llama-3.3-70b": (0.0, 0.0),
    "deepseek-coder": (0.0, 0.0),
    "deepseek-r1": (0.0, 0.0),
    "mistral-7b": (0.0, 0.0),
    "qwen-2.5-coder": (0.0, 0.0),
    "local": (0.0, 0.0),
}

DEFAULT_PRICING: Tuple[float, float] = (2.00, 8.00)

def get_model_pricing(model: str) -> Tuple[float, float]:
    """Return (prompt_price_per_m, completion_price_per_m) for given model string."""
    m_lower = model.lower().strip()
    # 1. Exact match
    if m_lower in MODEL_PRICING:
        return MODEL_PRICING[m_lower]
    # 2. Match longest specific key first
    for key in sorted(MODEL_PRICING.keys(), key=len, reverse=True):
        if key in m_lower:
            return MODEL_PRICING[key]
    return DEFAULT_PRICING

def calculate_token_costs(
    model: str,
    candidate_tokens: int,
    selected_tokens: int,
    output_tokens: int = 0,
    cache_hit_tokens: int = 0,
) -> Tuple[float, float, float]:
    """
    Calculate (cost_without_usd, cost_with_usd, cost_saved_usd).
    - Cost without ContextOS: full candidate tokens charged as prompt input + output tokens.
    - Cost with ContextOS: only selected tokens charged as prompt input (factoring cache hits) + output tokens.
    - Cost saved: cost_without_usd - cost_with_usd.
    """
    prompt_rate, completion_rate = get_model_pricing(model)

    # Convert prices from per million to per token
    prompt_price_per_token = prompt_rate / 1_000_000.0
    completion_price_per_token = completion_rate / 1_000_000.0

    # Prompt caching discount: cached tokens typically receive ~50% discount on input
    cached_discount_rate = prompt_price_per_token * 0.5

    # Cost without ContextOS (Raw candidate repository dump + full outputs)
    cost_without = (candidate_tokens * prompt_price_per_token) + (output_tokens * completion_price_per_token)

    # Cost with ContextOS (Budget-selected tokens - cached discount + outputs)
    uncached_selected = max(0, selected_tokens - cache_hit_tokens)
    cost_with = (
        (uncached_selected * prompt_price_per_token)
        + (cache_hit_tokens * cached_discount_rate)
        + (output_tokens * completion_price_per_token)
    )

    cost_saved = max(0.0, cost_without - cost_with)
    return round(cost_without, 6), round(cost_with, 6), round(cost_saved, 6)
