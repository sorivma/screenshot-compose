"""Registry selecting isolated highlighters without coupling language modules."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

from .model import HighlightToken
from .provider import HighlightProvider
from .pygments_provider import PygmentsProvider


@dataclass(frozen=True)
class ProviderSpec:
    module: str
    class_name: str
    aliases: tuple[str, ...]
    suffixes: tuple[str, ...]


_FALLBACK = PygmentsProvider()
_SPECS = (
    ProviderSpec(".languages.go", "GoProvider", ("go", "golang"), (".go",)),
    ProviderSpec(".languages.python", "PythonProvider", ("python", "py", "python3"), (".py",)),
    ProviderSpec(".languages.java", "JavaProvider", ("java",), (".java",)),
    ProviderSpec(
        ".languages.javascript",
        "JavaScriptProvider",
        ("javascript", "js", "jsx", "typescript", "ts", "tsx", "vue"),
        (".js", ".jsx", ".ts", ".tsx", ".vue"),
    ),
)
_BY_ALIAS = {alias: spec for spec in _SPECS for alias in spec.aliases}
_BY_SUFFIX = {suffix: spec for spec in _SPECS for suffix in spec.suffixes}
_LOADED: dict[ProviderSpec, HighlightProvider] = {}


def provider_for(language: str | None, filename: str | None) -> HighlightProvider:
    if language and language.lower() in _BY_ALIAS:
        return _load_provider(_BY_ALIAS[language.lower()])
    if not language and filename:
        spec = _BY_SUFFIX.get(Path(filename).suffix.lower())
        if spec is not None:
            return _load_provider(spec)
    return _FALLBACK


def highlight_source(source: str, language: str | None = None, filename: str | None = None) -> list[HighlightToken]:
    return provider_for(language, filename).highlight(source, language, filename)


def _load_provider(spec: ProviderSpec) -> HighlightProvider:
    provider = _LOADED.get(spec)
    if provider is None:
        module = import_module(spec.module, package=__package__)
        provider_class = getattr(module, spec.class_name)
        provider = provider_class()
        _LOADED[spec] = provider
    return provider
