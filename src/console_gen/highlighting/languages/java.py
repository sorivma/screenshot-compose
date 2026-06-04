"""Java highlighter enriching declarations, types, parameters, and members."""

from __future__ import annotations

from ..model import HighlightToken, TokenKind
from ..pygments_provider import PygmentsProvider
from ._shared import after_balanced, at, propagate_declarations, set_kind, significant_indices, text


class JavaProvider:
    aliases = ("java",)

    def __init__(self) -> None:
        self._fallback = PygmentsProvider()

    def highlight(self, source: str, language: str | None, filename: str | None) -> list[HighlightToken]:
        tokens = self._fallback.highlight(source, "java", filename)
        significant = significant_indices(tokens)
        self._classify_types(tokens)
        self._classify_type_declarations(tokens, significant)
        self._classify_methods_and_parameters(tokens, significant)
        self._classify_members(tokens, significant)
        propagate_declarations(tokens, {TokenKind.TYPE, TokenKind.METHOD, TokenKind.PARAMETER})
        return tokens

    @staticmethod
    def _classify_types(tokens: list[HighlightToken]) -> None:
        for index, token in enumerate(tokens):
            if token.kind == TokenKind.VARIABLE and token.text[:1].isupper():
                set_kind(tokens, index, TokenKind.TYPE)

    def _classify_methods_and_parameters(self, tokens: list[HighlightToken], significant: list[int]) -> None:
        for position, index in enumerate(significant):
            if tokens[index].kind != TokenKind.FUNCTION:
                continue
            set_kind(tokens, index, TokenKind.METHOD, "declaration")
            open_position = position + 1
            if text(tokens, significant, open_position) != "(":
                continue
            end = after_balanced(tokens, significant, open_position, "(", ")")
            for cursor in range(open_position + 1, max(open_position + 1, end - 1)):
                parameter_index = significant[cursor]
                token = tokens[parameter_index]
                following = text(tokens, significant, cursor + 1)
                if token.kind == TokenKind.VARIABLE and following in {",", ")"}:
                    set_kind(tokens, parameter_index, TokenKind.PARAMETER, "declaration")

    @staticmethod
    def _classify_type_declarations(tokens: list[HighlightToken], significant: list[int]) -> None:
        for position, index in enumerate(significant):
            value = tokens[index].text
            if value not in {"class", "interface", "enum", "record"}:
                continue
            name_index = at(significant, position + 1)
            if name_index is None:
                continue
            set_kind(tokens, name_index, TokenKind.TYPE, "declaration")
            if value != "record" or text(tokens, significant, position + 2) != "(":
                continue
            end = after_balanced(tokens, significant, position + 2, "(", ")")
            for cursor in range(position + 3, max(position + 3, end - 1)):
                component_index = significant[cursor]
                if tokens[component_index].kind == TokenKind.VARIABLE and text(tokens, significant, cursor + 1) in {",", ")"}:
                    set_kind(tokens, component_index, TokenKind.PROPERTY, "declaration")

    @staticmethod
    def _classify_members(tokens: list[HighlightToken], significant: list[int]) -> None:
        for position, index in enumerate(significant):
            if tokens[index].text != ".":
                continue
            member_index = at(significant, position + 1)
            if member_index is None:
                continue
            kind = TokenKind.METHOD if text(tokens, significant, position + 2) == "(" else TokenKind.PROPERTY
            set_kind(tokens, member_index, kind)
