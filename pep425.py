"""Provide support for PEP 425 compatibility tags triples."""
from __future__ import annotations

from typing import Any, Container, Sequence


INTERPRETER_SHORT_NAMES = {
    "python": "py",  # Generic.
    "cpython": "cp",
    "pypy": "pp",
    "ironpython": "ip",
    "jython": "jy",
}


class Tag:

    """Represent the interpreter/ABI/platform tag triple as specified by PEP 425."""

    def __init__(self, interpreter: str, abi: str, platform: str) -> None:
        """Initialize the instance attributes.

        If 'interpreter' represents an interpreter with a short name, then its
        short name will be saved.

        """
        self.interpreter = interpreter  # XXX Check for shortened name.
        self.abi = abi
        self.platform = platform

    def __str__(self) -> str:
        return f"{self.interpreter}-{self.abi}-{self.platform}"

    def __eq__(self, other: Any) -> bool:
        return (
            self.interpreter == other.interpreter
            and self.abi == other.abi
            and self.platform == other.platform
        )


def sys_tags() -> Sequence[Tag]:
    """Return the sequence of tag triples for the running interpreter.

    The order of the sequence corresponds to priority order for the interpreter,
    from most to least important.

    """
    # XXX Detect CPython for special handling.
    # XXX distribution: str = sys.implementation.name,
    # XXX version: str = sysconfig.get_config_var("py_version_nodot"),
    # XXX abi: str = sysconfig.get_config_var("SOABI"),
    # XXX platform: str = distutils.util.get_platform()


def parse_tag(tag: str) -> Container[Tag]:
    """Parse the tag triple.

    The result can be more than one tag triple due to the possibility of
    compressed tag triples.

    """


# XXX https://pypi.org/project/mysql-connector-python/#files
# XXX https://pypi.org/project/pip/#files
# XXX https://pypi.org/project/numpy/#files
