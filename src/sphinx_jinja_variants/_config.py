"""Read the named Jinja contexts registered with Sphinx."""

from collections.abc import Mapping
from typing import TypeGuard

from sphinx.config import Config

type Contexts = Mapping[str, Mapping[str, object]]


def _is_mapping(value: object, /) -> TypeGuard[Mapping[object, object]]:
    """Recognize a mapping whose entries can be checked."""
    return isinstance(value, Mapping)


def _is_contexts(value: object, /) -> TypeGuard[Contexts]:
    """Recognize named contexts with string variable names."""
    return _is_mapping(value) and all(
        isinstance(name, str)
        and _is_mapping(context)
        and all(isinstance(key, str) for key in context)
        for name, context in value.items()
    )


def read_contexts(*, config: Config, name: str) -> Contexts:
    """Return the configured mapping without copying it."""
    value: object = config[name]
    if not _is_contexts(value):
        msg = (
            f"{name} must map context names to mappings of template variables"
        )
        raise TypeError(msg)
    return value
