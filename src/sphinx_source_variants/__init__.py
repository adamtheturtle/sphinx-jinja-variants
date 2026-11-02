"""Render an RST composition with a scoped template context and source.

Callers choose variants and own presentation, source preparation, and content
validation. Standard section includes provide copied-target isolation. This
helper does not namespace targets created directly by renderer callbacks.
"""

from collections.abc import Callable, Mapping
from contextvars import ContextVar
from importlib.metadata import version
from pathlib import Path

from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from sphinx_section_include import resolve_source, section_source

__all__ = ["render_source_variant"]
__version__ = version(distribution_name="sphinx-source-variants")

_active_sources: ContextVar[tuple[tuple[int, str, Path], ...]] = ContextVar(
    "variant_sources", default=()
)


def render_source_variant(
    *,
    directive: SphinxDirective,
    source: str,
    context_name: str,
    context: Mapping[str, object],
    render: Callable[[nodes.document], list[nodes.Node]],
) -> list[nodes.Node]:
    """Prepare one source and run a renderer under temporary Jinja values.

    The selected named context inherits its original values. Bindings are
    restored after success, nested rendering, and exceptions. Values are not
    deep-copied; renderers should treat context data as read-only.

    The callback may prepare the yielded document before parsing its
    composition.
    Standard include-section directives reuse that document only within this
    invocation. Sequential variants parse sources afresh, with dependency
    tracking supplied by section_source. Nesting the same source in the same
    consuming document is rejected to avoid reusing another variant's tree.
    """
    source_key = (
        id(directive.env),
        directive.env.docname,
        resolve_source(directive=directive, source=source),
    )
    active = _active_sources.get()
    if source_key in active:
        message = "Cannot nest variants of the same source in one document"
        raise ValueError(message)
    contexts = directive.config.jinja2_contexts
    token = _active_sources.set((*active, source_key))
    try:
        directive.config.jinja2_contexts = {
            **contexts,
            context_name: {**contexts.get(context_name, {}), **context},
        }
        with section_source(
            directive=directive, source=source, docname=directive.env.docname
        ) as document:
            return render(document)
    finally:
        directive.config.jinja2_contexts = contexts
        _active_sources.reset(token)
