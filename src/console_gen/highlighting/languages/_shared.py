"""Small token-stream helpers shared by isolated language providers."""

from __future__ import annotations

from dataclasses import replace

from ..model import HighlightToken, TokenKind


def significant_indices(tokens: list[HighlightToken]) -> list[int]:
    return [index for index, token in enumerate(tokens) if token.text.strip()]


def at(significant: list[int], position: int) -> int | None:
    return significant[position] if 0 <= position < len(significant) else None


def text(tokens: list[HighlightToken], significant: list[int], position: int) -> str | None:
    index = at(significant, position)
    return tokens[index].text if index is not None else None


def set_kind(tokens: list[HighlightToken], index: int, kind: TokenKind, *modifiers: str) -> None:
    tokens[index] = replace(tokens[index], kind=kind, modifiers=frozenset(modifiers))


def after_balanced(
    tokens: list[HighlightToken],
    significant: list[int],
    start: int,
    opening: str,
    closing: str,
) -> int:
    depth = 0
    for position in range(start, len(significant)):
        value = tokens[significant[position]].text
        if value == opening:
            depth += 1
        elif value == closing:
            depth -= 1
            if depth == 0:
                return position + 1
    return len(significant)


def between(tokens: list[HighlightToken], start: int, end: int | None) -> str:
    return "".join(token.text for token in tokens[start + 1 : end]) if end is not None else ""


def propagate_declarations(tokens: list[HighlightToken], kinds: set[TokenKind]) -> None:
    declarations = {
        token.text: token.kind
        for token in tokens
        if "declaration" in token.modifiers and token.kind in kinds
    }
    for index, token in enumerate(tokens):
        if token.kind == TokenKind.VARIABLE and token.text in declarations:
            set_kind(tokens, index, declarations[token.text])
