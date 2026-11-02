Python API
==========

Import ``render_source_variant`` from ``sphinx_source_variants``.
The library provides a Python helper for custom directives.
Load ``sphinx_jinja2`` and ``sphinx_section_include`` in the consuming project's ``extensions``.

Call ``render_source_variant`` with these keyword arguments:

* ``directive``: the active ``SphinxDirective``.
* ``source``: an RST file within the Sphinx source directory, relative to the current document.
  A leading slash is relative to the source root.
* ``context_name``: the key in ``jinja2_contexts`` to override.
* ``context``: a mapping of temporary values, merged over that entry's original bindings.
* ``render``: a callback accepting the prepared ``docutils.nodes.document`` positionally and returning ``list[docutils.nodes.Node]``.

The helper returns the callback's nodes.
The callback may prepare the source tree before parsing a composition using ``directive.state.nested_parse``.
Standard ``include-section`` directives inside the callback reuse the prepared tree.
The source and its includes remain dependencies of the consuming document, including during incremental builds.

Scope and isolation
-------------------

Each sequential invocation prepares a fresh source under its own context.
The original context dictionary is restored by identity after success or an exception.
Other context entries are preserved.
A missing entry starts with empty bindings.
Values are not deep-copied: treat nested context data as read-only.

Nested calls may prepare different sources.
After an inner call finishes or fails, the outer bindings and prepared source remain active.
Nesting the same canonical source in the same consuming document raises ``ValueError`` because its prepared tree would otherwise be reused across contexts.
The source scope is cleared when the call exits.

When using standard section includes, copied targets and references are isolated automatically.
Callers must avoid duplicate targets in markup their callbacks create directly.
It does not choose variants, generate headings, filter content, or define export destinations.

Example
-------

The `platform documentation <https://github.com/adamtheturtle/sphinx-source-variants/tree/main/sample/source>`_ defines a custom directive in ``conf.py``.
It renders the same composition for Linux and macOS, retains admonitions, and uses ordinary section includes for references and shared prerequisites.
No platform vocabulary or presentation policy is built into the library.
