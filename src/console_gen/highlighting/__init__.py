"""Language-independent source highlighting."""

from .model import HighlightToken, TokenKind
from .registry import highlight_source, provider_for

__all__ = ["HighlightToken", "TokenKind", "highlight_source", "provider_for"]
