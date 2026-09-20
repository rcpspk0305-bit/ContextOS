import re
from typing import Optional

_tiktoken_encoder = None
try:
    import tiktoken
    _tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
except Exception:
    _tiktoken_encoder = None

def count_tokens(text: str) -> int:
    """
    Counts or accurately estimates tokens for text and code payloads.
    Uses tiktoken cl100k_base if available, with a fast, calibrated heuristic fallback.
    """
    if not text:
        return 0

    if _tiktoken_encoder is not None:
        try:
            return len(_tiktoken_encoder.encode(text, disallowed_special=()))
        except Exception:
            pass

    # Calibrated fallback for code + markdown
    # Splits by tokens/symbols/words
    # Standard code averaging ~3.7-4 chars/token
    words = len(text.split())
    chars = len(text)
    # Blended estimation: 0.7 * (chars / 3.8) + 0.3 * (words * 1.3)
    estimated = int(0.75 * (chars / 3.8) + 0.25 * (words * 1.35))
    return max(1, estimated)
