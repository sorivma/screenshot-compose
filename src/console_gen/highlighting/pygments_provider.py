"""Pygments fallback provider and token adapter."""

from __future__ import annotations

from pygments import lex
from pygments.lexers import TextLexer, get_lexer_by_name, guess_lexer, guess_lexer_for_filename
from pygments.token import Comment, Error, Generic, Keyword, Literal, Name, Number, Operator, Punctuation, String, Text

from .model import HighlightToken, TokenKind


class PygmentsProvider:
    aliases: tuple[str, ...] = ()

    def highlight(self, source: str, language: str | None, filename: str | None) -> list[HighlightToken]:
        lexer = self._select_lexer(source, language, filename)
        return [HighlightToken(text, token_kind(token_type)) for token_type, text in lex(source, lexer)]

    @staticmethod
    def _select_lexer(source: str, language: str | None, filename: str | None):
        if language:
            return get_lexer_by_name(language)
        if filename:
            try:
                return guess_lexer_for_filename(filename, source)
            except Exception:
                pass
        try:
            return guess_lexer(source)
        except Exception:
            return TextLexer()


def token_kind(token_type: object) -> TokenKind:
    mappings = (
        (Name.Function, TokenKind.FUNCTION),
        (Name.Class, TokenKind.TYPE),
        (Name.Builtin, TokenKind.BUILTIN),
        (Name.Decorator, TokenKind.DECORATOR),
        (Name.Tag, TokenKind.TAG),
        (Name.Attribute, TokenKind.ATTRIBUTE),
        (Name.Variable, TokenKind.VARIABLE),
        (Name.Namespace, TokenKind.NAMESPACE),
        (Name, TokenKind.VARIABLE),
        (Comment, TokenKind.COMMENT),
        (Keyword.Namespace, TokenKind.KEYWORD),
        (Keyword.Type, TokenKind.TYPE),
        (Keyword, TokenKind.KEYWORD),
        (String, TokenKind.STRING),
        (Number, TokenKind.NUMBER),
        (Literal, TokenKind.NUMBER),
        (Operator, TokenKind.OPERATOR),
        (Punctuation, TokenKind.PUNCTUATION),
        (Generic.Heading, TokenKind.HEADING),
        (Generic.Subheading, TokenKind.SUBHEADING),
        (Generic.Deleted, TokenKind.DELETED),
        (Generic.Inserted, TokenKind.INSERTED),
        (Error, TokenKind.ERROR),
        (Text, TokenKind.TEXT),
    )
    for pygments_kind, kind in mappings:
        if token_type in pygments_kind:
            return kind
    return TokenKind.TEXT
