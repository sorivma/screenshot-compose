"""Python highlighter enriching Pygments with structural token roles."""

from __future__ import annotations

import ast

from ..model import HighlightToken, TokenKind
from ..pygments_provider import PygmentsProvider
from ._shared import after_balanced, at, between, propagate_declarations, set_kind, significant_indices, text


class PythonProvider:
    aliases = ("python", "py", "python3")

    def __init__(self) -> None:
        self._fallback = PygmentsProvider()

    def highlight(self, source: str, language: str | None, filename: str | None) -> list[HighlightToken]:
        tokens = self._fallback.highlight(source, "python", filename)
        significant = significant_indices(tokens)
        method_names, property_names = self._ast_roles(source)
        self._classify_declarations(tokens, significant, method_names, property_names)
        self._classify_members_and_calls(tokens, significant)
        propagate_declarations(tokens, {TokenKind.TYPE, TokenKind.FUNCTION, TokenKind.METHOD, TokenKind.PARAMETER})
        return tokens

    def _classify_declarations(
        self,
        tokens: list[HighlightToken],
        significant: list[int],
        method_names: set[str],
        property_names: set[str],
    ) -> None:
        for position, index in enumerate(significant):
            value = tokens[index].text
            next_index = at(significant, position + 1)
            if value == "class" and next_index is not None:
                set_kind(tokens, next_index, TokenKind.TYPE, "declaration")
            elif value in {"def", "async"}:
                def_position = position + 1 if value == "async" and text(tokens, significant, position + 1) == "def" else position
                self._classify_function(tokens, significant, def_position, method_names)
            elif value in {"import", "from"}:
                self._classify_imports(tokens, significant, position)
            elif (
                tokens[index].kind == TokenKind.VARIABLE
                and value in property_names
                and text(tokens, significant, position + 1) == ":"
                and (position == 0 or "\n" in between(tokens, significant[position - 1], index))
            ):
                set_kind(tokens, index, TokenKind.PROPERTY, "declaration")

    def _classify_function(
        self,
        tokens: list[HighlightToken],
        significant: list[int],
        position: int,
        method_names: set[str],
    ) -> None:
        name_index = at(significant, position + 1)
        if name_index is None or text(tokens, significant, position) != "def":
            return
        kind = TokenKind.METHOD if tokens[name_index].text in method_names else TokenKind.FUNCTION
        set_kind(tokens, name_index, kind, "declaration")
        open_position = position + 2
        if text(tokens, significant, open_position) != "(":
            return
        end = after_balanced(tokens, significant, open_position, "(", ")")
        for cursor in range(open_position + 1, max(open_position + 1, end - 1)):
            index = significant[cursor]
            if tokens[index].kind not in {TokenKind.VARIABLE, TokenKind.BUILTIN}:
                continue
            previous = text(tokens, significant, cursor - 1)
            following = text(tokens, significant, cursor + 1)
            if previous not in {".", ":"} and following in {":", ",", ")", "="}:
                set_kind(tokens, index, TokenKind.PARAMETER, "declaration")

    def _classify_imports(self, tokens: list[HighlightToken], significant: list[int], position: int) -> None:
        cursor = position + 1
        while cursor < len(significant):
            index = significant[cursor]
            if "\n" in between(tokens, significant[cursor - 1], index):
                return
            token = tokens[index]
            if token.kind == TokenKind.VARIABLE:
                kind = TokenKind.TYPE if token.text[:1].isupper() else TokenKind.NAMESPACE
                set_kind(tokens, index, kind, "declaration")
            cursor += 1

    def _classify_members_and_calls(self, tokens: list[HighlightToken], significant: list[int]) -> None:
        for position, index in enumerate(significant):
            value = tokens[index].text
            if value == ".":
                member_index = at(significant, position + 1)
                if member_index is not None:
                    kind = TokenKind.METHOD if text(tokens, significant, position + 2) == "(" else TokenKind.PROPERTY
                    set_kind(tokens, member_index, kind)
            elif tokens[index].kind == TokenKind.VARIABLE and text(tokens, significant, position + 1) == "(":
                set_kind(tokens, index, TokenKind.TYPE if value[:1].isupper() else TokenKind.FUNCTION)
            elif (
                tokens[index].kind == TokenKind.VARIABLE
                and text(tokens, significant, position + 1) == "="
                and text(tokens, significant, position - 1) in {"(", ","}
            ):
                set_kind(tokens, index, TokenKind.PROPERTY)

    @staticmethod
    def _ast_roles(source: str) -> tuple[set[str], set[str]]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return set(), set()

        method_names: set[str] = set()
        property_names: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_names.add(child.name)
                elif isinstance(child, (ast.Assign, ast.AnnAssign)):
                    targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                    property_names.update(target.id for target in targets if isinstance(target, ast.Name))
        return method_names, property_names
