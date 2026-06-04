from pathlib import Path

from console_gen.highlighting import TokenKind, highlight_source, provider_for


def _kinds_by_text(source: str) -> dict[str, set[TokenKind]]:
    result: dict[str, set[TokenKind]] = {}
    for token in highlight_source(source, language="go", filename="example.go"):
        if token.text.strip():
            result.setdefault(token.text, set()).add(token.kind)
    return result


def test_registry_selects_isolated_providers_and_keeps_pygments_fallback():
    assert type(provider_for("go", None)).__name__ == "GoProvider"
    assert type(provider_for(None, "main.go")).__name__ == "GoProvider"
    assert type(provider_for("python", None)).__name__ == "PythonProvider"
    assert type(provider_for("java", None)).__name__ == "JavaProvider"
    assert type(provider_for("tsx", None)).__name__ == "JavaScriptProvider"
    assert type(provider_for("ruby", None)).__name__ == "PygmentsProvider"


def test_go_provider_enriches_declarations_and_references():
    source = """
package main

import "net/http"

type response struct {
    Status string
}

func health(w http.ResponseWriter) {
    w.Header()
    http.HandleFunc("/health", health)
    _ = response{Status: "ok"}
}

func (r response) render() string {
    return r.Status
}
"""
    tokens = highlight_source(source, language="go", filename="example.go")
    kinds: dict[str, set[TokenKind]] = {}
    for token in tokens:
        if token.text.strip():
            kinds.setdefault(token.text, set()).add(token.kind)

    assert TokenKind.NAMESPACE in kinds["main"]
    assert TokenKind.TYPE in kinds["response"]
    assert TokenKind.PROPERTY in kinds["Status"]
    assert TokenKind.FUNCTION in kinds["health"]
    assert TokenKind.PARAMETER in kinds["w"]
    assert TokenKind.NAMESPACE in kinds["http"]
    assert TokenKind.TYPE in kinds["ResponseWriter"]
    assert TokenKind.METHOD in kinds["Header"]
    assert TokenKind.FUNCTION in kinds["HandleFunc"]
    assert TokenKind.METHOD in kinds["render"]
    assert all(token.kind == TokenKind.PARAMETER for token in tokens if token.text == "w")


def test_go_example_produces_more_semantic_kinds_than_plain_pygments():
    source = Path("examples/inputs/server.go").read_text(encoding="utf-8")
    kinds = {token.kind for token in highlight_source(source, language="go", filename="server.go")}

    assert {TokenKind.TYPE, TokenKind.FUNCTION, TokenKind.METHOD, TokenKind.PARAMETER, TokenKind.PROPERTY} <= kinds


def test_python_provider_enriches_framework_code():
    source = Path("examples/inputs/fastapi_app.py").read_text(encoding="utf-8")
    tokens = highlight_source(source, language="python", filename="fastapi_app.py")
    kinds = {(token.text, token.kind) for token in tokens}

    assert ("Todo", TokenKind.TYPE) in kinds
    assert ("save_todo", TokenKind.FUNCTION) in kinds
    assert ("todo_id", TokenKind.PARAMETER) in kinds
    assert ("title", TokenKind.PROPERTY) in kinds
    assert ("post", TokenKind.METHOD) in kinds
    assert ("status_code", TokenKind.PROPERTY) in kinds


def test_python_provider_distinguishes_class_methods_and_module_variables():
    source = """
class Service:
    enabled: bool = True

    def run(self, value: str):
        return value

service: Service = Service()
"""
    tokens = highlight_source(source, language="python", filename="service.py")
    kinds = {(token.text, token.kind) for token in tokens}

    assert ("run", TokenKind.METHOD) in kinds
    assert ("self", TokenKind.PARAMETER) in kinds
    assert ("enabled", TokenKind.PROPERTY) in kinds
    assert ("service", TokenKind.PROPERTY) not in kinds


def test_java_provider_enriches_methods_parameters_and_types():
    source = Path("examples/inputs/SpringApplication.java").read_text(encoding="utf-8")
    tokens = highlight_source(source, language="java", filename="SpringApplication.java")
    kinds = {(token.text, token.kind) for token in tokens}

    assert ("DemoApplication", TokenKind.TYPE) in kinds
    assert ("main", TokenKind.METHOD) in kinds
    assert ("args", TokenKind.PARAMETER) in kinds
    assert ("run", TokenKind.METHOD) in kinds
    assert ("void", TokenKind.TYPE) in kinds
    assert ("message", TokenKind.PROPERTY) in kinds


def test_javascript_family_provider_enriches_tsx_and_vue_without_cross_language_rules():
    tsx = Path("examples/inputs/react-dashboard.tsx").read_text(encoding="utf-8")
    vue = Path("examples/inputs/vue-profile.vue").read_text(encoding="utf-8")
    tsx_kinds = {(token.text, token.kind) for token in highlight_source(tsx, language="tsx", filename="dashboard.tsx")}
    vue_tokens = highlight_source(vue, language="vue", filename="profile.vue")

    assert ("Metric", TokenKind.TYPE) in tsx_kinds
    assert ("Dashboard", TokenKind.FUNCTION) in tsx_kinds
    assert ("metric", TokenKind.PARAMETER) in tsx_kinds
    assert ("filter", TokenKind.METHOD) in tsx_kinds
    assert ("label", TokenKind.PROPERTY) in tsx_kinds
    assert ("ref", TokenKind.FUNCTION) in {(token.text, token.kind) for token in vue_tokens}
    assert not any(token.text == "=" and token.kind == TokenKind.TYPE for token in vue_tokens)


def test_javascript_provider_enriches_plain_js():
    source = """
export function greet(user) {
  const message = user.name.toUpperCase();
  return message;
}
"""
    kinds = {(token.text, token.kind) for token in highlight_source(source, language="javascript", filename="app.js")}

    assert ("greet", TokenKind.FUNCTION) in kinds
    assert ("user", TokenKind.PARAMETER) in kinds
    assert ("name", TokenKind.PROPERTY) in kinds
    assert ("toUpperCase", TokenKind.METHOD) in kinds
