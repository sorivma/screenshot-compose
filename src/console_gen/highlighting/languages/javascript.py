"""Shared structural highlighter for JavaScript, TypeScript, JSX, TSX, and Vue."""

from __future__ import annotations

from ..model import HighlightToken, TokenKind
from ..pygments_provider import PygmentsProvider
from ._shared import after_balanced, at, propagate_declarations, set_kind, significant_indices, text


class JavaScriptProvider:
    aliases = ("javascript", "js", "jsx", "typescript", "ts", "tsx", "vue")

    def __init__(self) -> None:
        self._fallback = PygmentsProvider()

    def highlight(self, source: str, language: str | None, filename: str | None) -> list[HighlightToken]:
        lexer = language or self._language_from_filename(filename)
        tokens = self._fallback.highlight(source, lexer, filename)
        significant = significant_indices(tokens)
        self._classify_declarations(tokens, significant)
        self._classify_parameters(tokens, significant)
        self._classify_properties(tokens, significant)
        self._classify_members_and_calls(tokens, significant)
        propagate_declarations(tokens, {TokenKind.TYPE, TokenKind.FUNCTION, TokenKind.PARAMETER, TokenKind.VARIABLE})
        return tokens

    def _classify_declarations(self, tokens: list[HighlightToken], significant: list[int]) -> None:
        for position, index in enumerate(significant):
            value = tokens[index].text
            next_index = at(significant, position + 1)
            if tokens[index].kind == TokenKind.KEYWORD and value in {"type", "interface", "class", "enum"} and next_index is not None:
                set_kind(tokens, next_index, TokenKind.TYPE, "declaration")
            elif tokens[index].kind == TokenKind.KEYWORD and value == "function" and next_index is not None:
                set_kind(tokens, next_index, TokenKind.FUNCTION, "declaration")
            elif tokens[index].kind == TokenKind.KEYWORD and value in {"const", "let", "var"}:
                self._classify_variable_declaration(tokens, significant, position)
            elif tokens[index].kind == TokenKind.VARIABLE and value[:1].isupper():
                set_kind(tokens, index, TokenKind.TYPE)

    def _classify_variable_declaration(self, tokens: list[HighlightToken], significant: list[int], position: int) -> None:
        cursor = position + 1
        while cursor < len(significant):
            index = significant[cursor]
            value = tokens[index].text
            if value in {"=", ";"}:
                return
            if tokens[index].kind == TokenKind.VARIABLE:
                set_kind(tokens, index, TokenKind.VARIABLE, "declaration")
            cursor += 1

    def _classify_parameters(self, tokens: list[HighlightToken], significant: list[int]) -> None:
        for position, index in enumerate(significant):
            if tokens[index].text != "(":
                continue
            end = after_balanced(tokens, significant, position, "(", ")")
            if text(tokens, significant, end) not in {"=>", "{", ":"}:
                previous_index = at(significant, position - 1)
                if previous_index is None or tokens[previous_index].kind != TokenKind.FUNCTION:
                    continue
            for cursor in range(position + 1, max(position + 1, end - 1)):
                parameter_index = significant[cursor]
                token = tokens[parameter_index]
                previous = text(tokens, significant, cursor - 1)
                following = text(tokens, significant, cursor + 1)
                if token.kind in {TokenKind.VARIABLE, TokenKind.PROPERTY} and previous != ":" and following in {":", ",", ")", "}"}:
                    set_kind(tokens, parameter_index, TokenKind.PARAMETER, "declaration")

    @staticmethod
    def _classify_properties(tokens: list[HighlightToken], significant: list[int]) -> None:
        for position, index in enumerate(significant):
            token = tokens[index]
            if (
                token.kind == TokenKind.VARIABLE
                and "declaration" not in token.modifiers
                and text(tokens, significant, position + 1) == ":"
            ):
                set_kind(tokens, index, TokenKind.PROPERTY, "declaration")

    @staticmethod
    def _classify_members_and_calls(tokens: list[HighlightToken], significant: list[int]) -> None:
        for position, index in enumerate(significant):
            value = tokens[index].text
            if value == ".":
                member_index = at(significant, position + 1)
                if member_index is not None:
                    kind = TokenKind.METHOD if text(tokens, significant, position + 2) == "(" else TokenKind.PROPERTY
                    set_kind(tokens, member_index, kind)
            elif tokens[index].kind == TokenKind.VARIABLE and text(tokens, significant, position + 1) == "(":
                set_kind(tokens, index, TokenKind.FUNCTION)
            elif tokens[index].kind == TokenKind.VARIABLE and text(tokens, significant, position + 1) == ":":
                set_kind(tokens, index, TokenKind.PROPERTY)

    @staticmethod
    def _language_from_filename(filename: str | None) -> str:
        suffixes = {
            ".js": "javascript",
            ".jsx": "jsx",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".vue": "vue",
        }
        if filename:
            for suffix, language in suffixes.items():
                if filename.lower().endswith(suffix):
                    return language
        return "javascript"
