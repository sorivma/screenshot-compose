"""Go highlighter with structural enrichment over the Pygments lexer."""

from __future__ import annotations

import re
from dataclasses import replace

from ..model import HighlightToken, TokenKind
from ..pygments_provider import PygmentsProvider


class GoProvider:
    aliases = ("go", "golang")

    def __init__(self) -> None:
        self._fallback = PygmentsProvider()

    def highlight(self, source: str, language: str | None, filename: str | None) -> list[HighlightToken]:
        tokens = self._fallback.highlight(source, "go", filename)
        significant = [index for index, token in enumerate(tokens) if token.text.strip()]
        self._classify_declarations(tokens, significant)
        self._classify_selectors(tokens, significant, self._imported_packages(source))
        self._classify_calls(tokens, significant)
        self._classify_references(tokens, significant)
        return tokens

    def _classify_declarations(self, tokens: list[HighlightToken], significant: list[int]) -> None:
        for position, index in enumerate(significant):
            text = tokens[index].text
            next_index = self._at(significant, position + 1)
            if text == "package" and next_index is not None:
                self._set(tokens, next_index, TokenKind.NAMESPACE, "declaration")
            elif text == "type" and next_index is not None:
                self._set(tokens, next_index, TokenKind.TYPE, "declaration")
            elif text == "func":
                self._classify_function_declaration(tokens, significant, position)
            elif text in {"var", "const"} and next_index is not None:
                self._set(tokens, next_index, TokenKind.VARIABLE, "declaration")
            elif text == ":=":
                self._classify_short_declaration(tokens, significant, position)
            elif text == "struct":
                self._classify_struct_fields(tokens, significant, position)

    def _classify_function_declaration(
        self,
        tokens: list[HighlightToken],
        significant: list[int],
        position: int,
    ) -> None:
        cursor = position + 1
        is_method = False
        if self._text(tokens, significant, cursor) == "(":
            is_method = True
            self._classify_parameters(tokens, significant, cursor)
            cursor = self._after_balanced(tokens, significant, cursor, "(", ")")
        name_index = self._at(significant, cursor)
        if name_index is None:
            return
        self._set(tokens, name_index, TokenKind.METHOD if is_method else TokenKind.FUNCTION, "declaration")
        parameters_start = cursor + 1
        if self._text(tokens, significant, parameters_start) == "(":
            self._classify_parameters(tokens, significant, parameters_start)

    def _classify_parameters(self, tokens: list[HighlightToken], significant: list[int], start: int) -> None:
        end = self._after_balanced(tokens, significant, start, "(", ")")
        for position in range(start + 1, max(start + 1, end - 1)):
            index = significant[position]
            token = tokens[index]
            next_text = self._text(tokens, significant, position + 1)
            previous_text = self._text(tokens, significant, position - 1)
            if token.kind == TokenKind.VARIABLE and next_text not in {".", ",", ")"} and previous_text != ".":
                self._set(tokens, index, TokenKind.PARAMETER, "declaration")

    def _classify_struct_fields(self, tokens: list[HighlightToken], significant: list[int], position: int) -> None:
        open_position = position + 1
        if self._text(tokens, significant, open_position) != "{":
            return
        depth = 0
        line_start = True
        for cursor in range(open_position + 1, len(significant)):
            index = significant[cursor]
            text = tokens[index].text
            if text == "{":
                depth += 1
            elif text == "}":
                if depth == 0:
                    return
                depth -= 1
            elif depth == 0 and line_start and tokens[index].kind == TokenKind.VARIABLE:
                self._set(tokens, index, TokenKind.PROPERTY, "declaration")
            line_start = "\n" in self._between(tokens, index, self._at(significant, cursor + 1))

    def _classify_short_declaration(
        self,
        tokens: list[HighlightToken],
        significant: list[int],
        position: int,
    ) -> None:
        cursor = position - 1
        while cursor >= 0:
            index = significant[cursor]
            text = tokens[index].text
            if text in {";", "{", "}"} or "\n" in self._between(tokens, index, significant[cursor + 1]):
                return
            if tokens[index].kind == TokenKind.VARIABLE:
                self._set(tokens, index, TokenKind.VARIABLE, "declaration")
            cursor -= 1

    def _classify_selectors(
        self,
        tokens: list[HighlightToken],
        significant: list[int],
        imported_packages: set[str],
    ) -> None:
        for position, index in enumerate(significant):
            if tokens[index].text != ".":
                continue
            owner_index = self._at(significant, position - 1)
            member_index = self._at(significant, position + 1)
            if owner_index is None or member_index is None:
                continue
            owner_is_package = tokens[owner_index].text in imported_packages
            if owner_is_package:
                self._set(tokens, owner_index, TokenKind.NAMESPACE)
            if self._text(tokens, significant, position + 2) == "(":
                member_kind = TokenKind.FUNCTION if owner_is_package else TokenKind.METHOD
            else:
                member_kind = TokenKind.TYPE if owner_is_package else TokenKind.PROPERTY
            self._set(tokens, member_index, member_kind)

    def _classify_calls(self, tokens: list[HighlightToken], significant: list[int]) -> None:
        for position, index in enumerate(significant):
            if tokens[index].kind != TokenKind.VARIABLE:
                continue
            if self._text(tokens, significant, position + 1) == "(":
                self._set(tokens, index, TokenKind.FUNCTION)

    def _classify_references(self, tokens: list[HighlightToken], significant: list[int]) -> None:
        declarations = {
            token.text: token.kind
            for token in tokens
            if "declaration" in token.modifiers
            and token.kind in {TokenKind.FUNCTION, TokenKind.METHOD, TokenKind.PARAMETER, TokenKind.TYPE}
        }
        for position, index in enumerate(significant):
            token = tokens[index]
            if token.kind != TokenKind.VARIABLE:
                continue
            if self._text(tokens, significant, position + 1) == ":":
                self._set(tokens, index, TokenKind.PROPERTY)
            elif token.text in declarations:
                self._set(tokens, index, declarations[token.text])

    @staticmethod
    def _imported_packages(source: str) -> set[str]:
        packages: set[str] = set()
        import_blocks = re.findall(r"\bimport\s*\((.*?)\)", source, flags=re.DOTALL)
        import_blocks.extend(re.findall(r'\bimport\s+([^\n]+)', source))
        for block in import_blocks:
            for alias, path in re.findall(r'(?:^|\s)([A-Za-z_]\w*|\.)?\s*"([^"]+)"', block):
                if alias != ".":
                    packages.add(alias or path.rsplit("/", 1)[-1])
        return packages

    @staticmethod
    def _set(tokens: list[HighlightToken], index: int, kind: TokenKind, *modifiers: str) -> None:
        tokens[index] = replace(tokens[index], kind=kind, modifiers=frozenset(modifiers))

    @staticmethod
    def _at(significant: list[int], position: int) -> int | None:
        return significant[position] if 0 <= position < len(significant) else None

    @classmethod
    def _text(cls, tokens: list[HighlightToken], significant: list[int], position: int) -> str | None:
        index = cls._at(significant, position)
        return tokens[index].text if index is not None else None

    @classmethod
    def _after_balanced(
        cls,
        tokens: list[HighlightToken],
        significant: list[int],
        start: int,
        opening: str,
        closing: str,
    ) -> int:
        depth = 0
        for position in range(start, len(significant)):
            text = tokens[significant[position]].text
            if text == opening:
                depth += 1
            elif text == closing:
                depth -= 1
                if depth == 0:
                    return position + 1
        return len(significant)

    @staticmethod
    def _between(tokens: list[HighlightToken], start: int, end: int | None) -> str:
        return "".join(token.text for token in tokens[start + 1 : end]) if end is not None else ""
