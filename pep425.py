"""Provide support for PEP 425 compatibility tags triples."""
from __future__ import annotations

import os
import pathlib
from typing import Any, Container, Sequence


INTERPRETER_SHORT_NAMES = {
    "python": "py",  # Generic.
    "cpython": "cp",
    "pypy": "pp",
    "ironpython": "ip",
    "jython": "jy",
}


# A dataclass would be better, but Python 2.7. :(
class Tag:

    """Representation of the interpreter/ABI/platform tag triple as specified by PEP 425."""

    def __init__(self, interpreter: str, abi: str, platform: str) -> None:
        """Initialize the instance attributes.

        All values are lowercased.

        """
        self._tags = interpreter.lower(), abi.lower(), platform.lower()

    def __eq__(self, other: Any) -> bool:
        return self._tags == other._tags

    def __hash__(self) -> int:
        return hash(self._tags)

    def __str__(self) -> str:
        return "-".join(self._tags)

    @property
    def interpreter(self) -> str:
        return self._tags[0]

    @property
    def abi(self) -> str:
        return self._tags[1]

    @property
    def platform(self) -> str:
        return self._tags[2]


def parse_tag(tag: str) -> Container[Tag]:
    """Parse the tag triple.

    The result can be more than one tag triple due to the possibility of
    compressed tag triples.

    """
    tags = set()
    interpreters, abis, platforms = tag.split("-")
    for interpreter in interpreters.split("."):
        for abi in abis.split("."):
            for platform in platforms.split("."):
                tags.add(Tag(interpreter, abi, platform))
    return frozenset(tags)


def parse_wheel_tag(path: os.PathLike) -> Container[Tag]:
    """Parse the path/filename of a wheel file for its tag triple(s)."""
    name = pathlib.PurePath(path).stem
    parts = 3
    index = len(name)
    while parts:
        index = name.rindex("-", 0, index)
        parts -= 1
    return parse_tag(name[index + 1 :])


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


# XXX https://pypi.org/project/mysql-connector-python/#files
# XXX https://pypi.org/project/pip/#files
# XXX https://pypi.org/project/numpy/#files
