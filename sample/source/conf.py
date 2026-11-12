"""Render installation instructions for two operating systems."""

# Sphinx requires lowercase names for its configuration settings.
# pylint: disable=invalid-name

from functools import partial
from typing import override

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import ExtensionMetadata

from sphinx_jinja_variants import render_source_variant

extensions = ["sphinx_jinja2", "sphinx_section_include"]
project = "Jinja variants example"
jinja2_contexts = {
    "installation": {
        "platform": "Default",
        "command": "Default instructions.",
        "config_path": "default.ini",
        "inherited": "Shared context value.",
    }
}
platform_contexts = {
    "linux": {
        "platform": "Linux",
        "command": "Linux installation.",
        "config_path": "/etc/example.ini",
    },
    "macos": {
        "platform": "macOS",
        "command": "macOS installation.",
        "config_path": "~/Library/example.ini",
    },
}


class PlatformInstructions(SphinxDirective):
    """A second consumer choosing platform contexts and its own
    presentation.
    """

    required_arguments = 1
    has_content = True

    @override
    def run(self) -> list[nodes.Node]:
        """Render installation excerpts under independently chosen
        contexts.
        """
        output: list[nodes.Node] = []
        for key, context in self.config.platform_contexts.items():
            output.extend(
                render_source_variant(
                    directive=self,
                    source=self.arguments[0],
                    context_name="installation",
                    context=context,
                    render=partial(self._render, key=key),
                )
            )
        return output

    def _render(
        self, _document: nodes.document, /, *, key: str
    ) -> list[nodes.Node]:
        """Keep all source content and use an ordinary document
        container.
        """
        container = nodes.container(classes=["platform-" + key])
        _ = self.state.nested_parse(
            block=self.content,
            input_offset=self.content_offset,
            node=container,
        )
        return [container]


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register this consumer's directive and variant choices."""
    app.add_config_value(
        name="platform_contexts", default={}, rebuild="env", types=dict
    )
    app.add_directive(name="platform-instructions", cls=PlatformInstructions)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
