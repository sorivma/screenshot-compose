"""Contracts for isolated language highlighting providers."""

from __future__ import annotations

from typing import Protocol

from .model import HighlightToken


class HighlightProvider(Protocol):
    aliases: tuple[str, ...]

    def highlight(self, source: str, language: str | None, filename: str | None) -> list[HighlightToken]:
        ...
