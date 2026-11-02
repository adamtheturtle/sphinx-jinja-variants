"""Platform documentation exercises scoped source variants."""

from collections import Counter
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import override

import pytest
from bs4 import BeautifulSoup
from docutils import nodes
from sphinx.errors import SphinxWarning
from sphinx.testing.util import SphinxTestApp
from sphinx.util.docutils import SphinxDirective

from sphinx_jinja_variants import render_source_variant


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
                    prepare=(
                        self._prepare
                        if self.config.prepare_platform_sources
                        else None
                    ),
                )
            )
        return output

    def _prepare(self, document: nodes.document, /) -> None:
        """Apply this consumer's policy under the active platform
        context.
        """
        platform = self.config.jinja2_contexts["installation"]["platform"]
        for paragraph in document.findall(condition=nodes.paragraph):
            if paragraph.astext().startswith("Preparation target:"):
                paragraph[:] = [
                    nodes.Text(data="Prepared for " + platform + ".")
                ]

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


def write_platform_project(*, root: Path) -> None:
    """Create real platform documentation with templates, includes, and
    references.
    """
    root.mkdir()
    files = {
        "conf.py": (
            "extensions = ['sphinx_jinja2', 'sphinx_section_include']\n\n"
            "def setup(app):\n"
            "    app.add_config_value(name='platform_contexts', default={},\n"
            "                         rebuild='env', types=dict)\n"
            "    app.add_config_value(name='prepare_platform_sources',\n"
            "                         default=False,\n"
            "                         rebuild='env', types=bool)\n"
        ),
        "index.rst": (
            "Platforms\n=========\n\n.. toctree::\n\n   install\n   extra\n\n"
            ".. platform-instructions:: install.rst\n\n"
            "   .. include-section:: install.rst\n      :section: Install\n"
            "      :include-heading:\n"
            "      :heading-style: rubric\n\n"
            "   .. include-section:: install.rst\n      :section: Install\n"
            "      :include-heading:\n"
            "      :heading-style: rubric\n\n"
            "   .. include-section:: extra.rst\n      :section: Extra\n"
            "      :heading-style: rubric\n"
        ),
        "install.rst": (
            "Platform manual\n===============\n\n"
            ".. jinja:: installation\n\n"
            "   .. parse-probe:: {{ platform }}\n\n"
            "   Install\n   -------\n\n"
            "   {{ command }}\n\n   {{ inherited }}\n\n"
            "   Preparation target: primary.\n\n"
            "   .. include:: shared.txt\n\n"
            "   .. _verify:\n\n   Verify\n   ~~~~~~\n\n"
            "   Open ``{{ config_path }}``. See :ref:`verify`.\n\n"
            "   .. note:: Keep this installation advice.\n"
        ),
        "shared.txt": "Original shared prerequisite.\n",
        "extra.rst": "Additional source\n=================\n\nExtra\n-----\n\n"
        "Preparation target: extra.\n",
    }
    for name, content in files.items():
        _ = (root / name).write_text(data=content)


def platform_configuration() -> dict[str, object]:
    """Supply operating-system variants rather than language or question
    data.
    """
    return {
        "jinja2_contexts": {
            "installation": {
                "platform": "Default",
                "command": "Default instructions.",
                "config_path": "default.ini",
                "inherited": "Shared context value.",
            },
            "unrelated": {"sentinel": "Preserve another named context."},
        },
        "platform_contexts": {
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
        },
    }


def _assert_platform_content(
    *, container: nodes.container, platform: str, other: str, prepared: bool
) -> None:
    """Preserve content while checking platform and preparation
    isolation.
    """
    text = container.astext()
    assert platform + " installation." in text
    assert other + " installation." not in text
    assert "Shared context value." in text
    assert "Original shared prerequisite." in text
    assert "Keep this installation advice." in text
    if prepared:
        expected_preparations = 3
        assert (
            text.count("Prepared for " + platform + ".")
            == expected_preparations
        )
        assert "Preparation target:" not in text
    else:
        assert "Preparation target: primary." in text
        assert "Preparation target: extra." in text
    expected_copies = 2
    assert (
        len(list(container.findall(condition=nodes.note))) == expected_copies
    )


def _assert_local_links(*, page: Path) -> None:
    """Require unique targets and links confined to each platform."""
    soup = BeautifulSoup(
        markup=page.read_text(),
        features="html.parser",
    )
    ids = [str(object=node["id"]) for node in soup.select(selector="[id]")]
    assert len(ids) == len(set(ids))
    for key in ("linux", "macos"):
        html_container = soup.select_one(selector=".platform-" + key)
        assert html_container is not None
        for link in html_container.select(selector='a[href^="#"]'):
            assert (
                html_container.find(id=str(object=link["href"])[1:])
                is not None
            )


@pytest.mark.parametrize(argnames="buildername", argvalues=["html", "text"])
@pytest.mark.parametrize(argnames="prepared", argvalues=[False, True])
def test_platform_variants_references_dependencies_and_contexts(
    *,
    make_app: Callable[..., SphinxTestApp],
    tmp_path: Path,
    buildername: str,
    prepared: bool,
) -> None:
    """A second consumer preserves all content and isolates source
    excerpts.
    """
    source = tmp_path / "source"
    write_platform_project(root=source)
    extra = source / "extra.rst"
    _ = extra.write_text(data=extra.read_text() + "\n.. context-probe::\n")
    collected: list[tuple[str, str]] = []
    reads: list[str] = []

    class Probe(SphinxDirective):
        """Count actual source parsing for each active platform."""

        required_arguments = 1

        @override
        def run(self) -> list[nodes.Node]:
            """Record a parse without adding output."""
            reads.append(self.arguments[0])
            return []

    class ContextProbe(SphinxDirective):
        """Observe the context used by collectors in additional
        sources.
        """

        @override
        def run(self) -> list[nodes.Node]:
            """Record the active document and selected platform."""
            collected.append(
                (
                    self.env.docname,
                    self.config.jinja2_contexts["installation"]["platform"],
                )
            )
            return []

    config = platform_configuration()
    config["prepare_platform_sources"] = prepared
    app = make_app(
        srcdir=source,
        buildername=buildername,
        confoverrides=config,
        exception_on_warning=True,
    )
    app.add_directive(name="platform-instructions", cls=PlatformInstructions)
    app.add_directive(name="parse-probe", cls=Probe)
    app.add_directive(name="context-probe", cls=ContextProbe)
    contexts = app.config.jinja2_contexts
    app.build()
    assert app.config.jinja2_contexts is contexts
    assert (
        app.config.jinja2_contexts
        == platform_configuration()["jinja2_contexts"]
    )
    assert Counter(reads) == Counter({"Linux": 1, "macOS": 1, "Default": 1})
    target_docname = "index" if prepared else "extra"
    assert Counter(collected) == Counter(
        [
            ("extra", "Default"),
            (target_docname, "Linux"),
            (target_docname, "macOS"),
        ]
    )
    tree = app.env.get_doctree(docname="index")
    containers = [
        node
        for node in tree.findall(condition=nodes.container)
        if "platform-linux" in node["classes"]
        or "platform-macos" in node["classes"]
    ]
    expected_platforms = 2
    assert len(containers) == expected_platforms
    for container, platform, other in zip(
        containers, ("Linux", "macOS"), ("macOS", "Linux"), strict=True
    ):
        _assert_platform_content(
            container=container,
            platform=platform,
            other=other,
            prepared=prepared,
        )
    if buildername == "html":
        _assert_local_links(page=Path(app.outdir) / "index.html")
    shared = source / "shared.txt"
    _ = shared.write_text(data="Changed shared prerequisite.\n")
    app.build()
    text = app.env.get_doctree(docname="index").astext()
    assert "Changed shared prerequisite." in text
    assert "Original shared prerequisite." not in text
    assert app.config.jinja2_contexts is contexts
    assert app.warning.getvalue() == ""


@pytest.mark.parametrize(
    argnames="failure", argvalues=["none", "renderer", "preparation"]
)
def test_nested_scopes_and_sequential_recovery(
    *,
    make_app: Callable[..., SphinxTestApp],
    tmp_path: Path,
    failure: str,
) -> None:
    """Nested sources restore their caller, and same-source aliases are
    rejected.
    """
    source = tmp_path / "source"
    source.mkdir()
    _ = (source / "conf.py").write_text(
        data="extensions = ['sphinx_jinja2', 'sphinx_section_include']\n"
    )
    _ = (source / "index.rst").write_text(
        data="Scopes\n======\n\n.. toctree::\n\n   outer\n   inner\n\n"
        ".. nested-variants::\n"
    )
    for name in ("outer", "inner"):
        _ = (source / (name + ".rst")).write_text(
            data="Source\n======\n\n.. jinja:: installation\n\n"
            "   {{ platform }} source.\n"
        )
    observations: list[str] = []

    class NestedVariants(SphinxDirective):
        """Exercise context scopes while Sphinx parses an actual
        composition.
        """

        @override
        def run(self) -> list[nodes.Node]:
            """Render nested sources followed by another sequential
            variant.
            """
            contexts = self.config.jinja2_contexts
            output = render_source_variant(
                directive=self,
                source="outer.rst",
                context_name="installation",
                context={"platform": "Outer"},
                render=self._outer,
            )
            assert self.config.jinja2_contexts is contexts
            output.extend(
                render_source_variant(
                    directive=self,
                    source="outer.rst",
                    context_name="installation",
                    context={"platform": "After"},
                    render=self._record,
                )
            )
            assert self.config.jinja2_contexts is contexts
            return output

        @staticmethod
        def _record(document: nodes.document, /) -> list[nodes.Node]:
            """Record the source parsed under this invocation's
            bindings.
            """
            observations.extend(
                node.astext()
                for node in document.findall(condition=nodes.paragraph)
            )
            return []

        def _inner(self, document: nodes.document, /) -> list[nodes.Node]:
            """Optionally fail after observing the nested variant."""
            _ = self._record(document)
            if failure == "renderer":
                message = "Inner renderer failed"
                raise ValueError(message)
            return []

        def _prepare_inner(self, document: nodes.document, /) -> None:
            """Observe temporary bindings and optionally fail during
            preparation.
            """
            assert (
                self.config.jinja2_contexts["installation"]["platform"]
                == "Inner"
            )
            if failure == "preparation":
                _ = self._record(document)
                message = "Inner preparation failed"
                raise ValueError(message)

        def _outer(self, document: nodes.document, /) -> list[nodes.Node]:
            """Protect the outer tree and restore outer bindings after
            inner work.
            """
            _ = self._record(document)
            contexts = self.config.jinja2_contexts
            with pytest.raises(
                expected_exception=ValueError,
                match="Cannot nest variants of the same source",
            ):
                _ = render_source_variant(
                    directive=self,
                    source="./outer.rst",
                    context_name="installation",
                    context={"platform": "Wrong"},
                    render=self._record,
                )
            assert self.config.jinja2_contexts is contexts
            if failure != "none":
                with pytest.raises(
                    expected_exception=ValueError,
                    match="Inner " + failure + " failed",
                ):
                    _ = render_source_variant(
                        directive=self,
                        source="inner.rst",
                        context_name="installation",
                        context={"platform": "Inner"},
                        render=self._inner,
                        prepare=self._prepare_inner,
                    )
            else:
                _ = render_source_variant(
                    directive=self,
                    source="inner.rst",
                    context_name="installation",
                    context={"platform": "Inner"},
                    render=self._inner,
                    prepare=self._prepare_inner,
                )
            assert self.config.jinja2_contexts is contexts
            assert contexts["installation"]["platform"] == "Outer"
            _ = self._record(document)
            return []

    app = make_app(
        srcdir=source,
        confoverrides={
            "jinja2_contexts": platform_configuration()["jinja2_contexts"]
        },
        exception_on_warning=True,
    )
    app.add_directive(name="nested-variants", cls=NestedVariants)
    contexts = app.config.jinja2_contexts
    app.build()
    assert observations == [
        "Outer source.",
        "Inner source.",
        "Outer source.",
        "After source.",
    ]
    assert app.config.jinja2_contexts is contexts
    assert app.warning.getvalue() == ""


@pytest.mark.parametrize(argnames="failure", argvalues=["source", "renderer"])
def test_context_restoration_after_failure(
    *, make_app: Callable[..., SphinxTestApp], tmp_path: Path, failure: str
) -> None:
    """Neither a source error nor a renderer error leaks overridden values."""
    source = tmp_path / "source"
    write_platform_project(root=source)
    if failure == "source":
        _ = (source / "install.rst").write_text(
            data=".. include:: absent.txt\n"
        )
    else:
        guide = source / "install.rst"
        _ = guide.write_text(
            data=guide.read_text().replace(
                "   .. parse-probe:: {{ platform }}\n\n", ""
            )
        )
        index = source / "index.rst"
        _ = index.write_text(
            data=index.read_text().replace(
                ":section: Install", ":section: Absent"
            )
        )
    app = make_app(
        srcdir=source,
        confoverrides=platform_configuration(),
        exception_on_warning=True,
    )
    app.add_directive(name="platform-instructions", cls=PlatformInstructions)
    contexts = app.config.jinja2_contexts
    with pytest.raises(
        expected_exception=SphinxWarning,
        match="absent.txt" if failure == "source" else "Expected one section",
    ):
        app.build()
    assert app.config.jinja2_contexts is contexts
