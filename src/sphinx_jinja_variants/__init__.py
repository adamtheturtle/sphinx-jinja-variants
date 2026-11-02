"""Render RST compositions with scoped Jinja contexts and prepared sources.

Callers choose variants and own presentation, source preparation, and content
validation. Standard section includes provide copied-target isolation. This
helper does not namespace targets created directly by renderer callbacks.
"""

from collections.abc import Callable, Mapping
from contextlib import nullcontext
from contextvars import ContextVar
from importlib.metadata import version
from pathlib import Path

from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from sphinx_section_include import (
    prepare_sources,
    resolve_source,
    section_source,
)

__all__ = ["render_source_variant"]
__version__ = version(distribution_name="sphinx-jinja-variants")

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
    prepare: Callable[[nodes.document], None] | None = None,
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

    A preparation callback runs under these Jinja values for primary and
    additional section sources, before section selection. When omitted,
    any surrounding source preparation remains active.
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
        preparation = (
            nullcontext()
            if prepare is None
            else prepare_sources(
                directive=directive,
                prepare=prepare,
                docname=directive.env.docname,
            )
        )
        with (
            preparation,
            section_source(
                directive=directive,
                source=source,
                docname=directive.env.docname,
            ) as document,
        ):
            return render(document)
    finally:
        directive.config.jinja2_contexts = contexts
        _active_sources.reset(token)
