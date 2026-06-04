"""Shared token model used by language-specific highlighters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenKind(str, Enum):
    TEXT = "text"
    COMMENT = "comment"
    KEYWORD = "keyword"
    NAMESPACE = "namespace"
    TYPE = "type"
    FUNCTION = "function"
    METHOD = "method"
    PARAMETER = "parameter"
    VARIABLE = "variable"
    PROPERTY = "property"
    BUILTIN = "builtin"
    DECORATOR = "decorator"
    TAG = "tag"
    ATTRIBUTE = "attribute"
    STRING = "string"
    NUMBER = "number"
    OPERATOR = "operator"
    PUNCTUATION = "punctuation"
    HEADING = "heading"
    SUBHEADING = "subheading"
    DELETED = "deleted"
    INSERTED = "inserted"
    ERROR = "error"


@dataclass(frozen=True)
class HighlightToken:
    text: str
    kind: TokenKind
    modifiers: frozenset[str] = frozenset()
