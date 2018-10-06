"""Provide support for PEP 425 compatibility tags triples."""
from __future__ import annotations

import distutils.util
import os
import pathlib
import platform
import sys
import sysconfig
from typing import Any, Container, Iterable, List, Sequence, Tuple


INTERPRETER_SHORT_NAMES = {
    "python": "py",  # Generic.
    "cpython": "cp",
    "pypy": "pp",
    "ironpython": "ip",
    "jython": "jy",
}


_32_BIT_INTERPRETER = sys.maxsize <= 2 ** 32


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
    """Parse the path of a wheel file for its tag triple(s)."""
    name = pathlib.PurePath(path).stem
    parts = 3
    index = len(name)
    while parts:
        index = name.rindex("-", 0, index)
        parts -= 1
    return parse_tag(name[index + 1 :])


def _cpython_tags(py_version, platforms) -> Iterable[Tag]:
    interpreter_version = sysconfig.get_config_var("py_version_nodot")
    interpreter = f"cp{interpreter_version}"  # XXX Python 2.7
    # XXX ABIs: 37m, abi3, none
    # XXX independent tags w/o ABIs
    # XXX independent tags w/o platforms
    raise NotImplementedError


def _pypy_tags(py_version, platforms) -> Iterable[Tag]:
    interpreter_version = (
        f"{py_version[0]}{sys.pypy_version_info.major}{sys.pypy_version_info.minor}"
    )  # XXX Python 2.7
    interpreter = f"pp{interpreter_version}"  # XXX Python 2.7
    # XXX
    raise NotImplementedError


def _generic_tags(py_version, interpreter_name, platforms) -> Iterable[Tag]:
    interpreter_version = sysconfig.get_config_var("py_version_nodot")
    if not interpreter_version:
        interpreter_version = "".join(py_version)
    interpreter = f"{interpreter_name}{interpreter_version}"  # XXX Python 2.7
    # XXX ABI
    # XXX
    raise NotImplementedError


def _py_version_range(py_version, end=0) -> Iterable[str]:
    """Yield Python versions in descending order.

    After the latest version, the major-only version will be yielded, and then
    all following versions up to 'end'.

    """
    yield f"py{py_version[0]}{py_version[1]}"
    yield f"py{py_version[0]}"
    for minor in range(py_version - 1, end - 1, -1):
        yield f"py{py_version[0]}{minor}"


def _independent_tags(py_version, platforms=["any"]) -> Iterable[Tag]:
    """Return a sequence of tags that are interpreter- and ABI-independent."""
    for version in _py_version_range(py_version):
        for platform in platforms:
            yield Tag(version, "none", platform)


def _mac_arch(arch, *, is_32bit=_32_BIT_INTERPRETER):
    """Calculate the CPU architecture for the interpreter on macOS."""
    if is_32bit:
        if arch.startswith("ppc"):
            return "ppc"
        else:
            return "i386"
    else:
        return arch


def _mac_binary_formats(version, cpu_arch: str) -> Sequence[str]:
    """Calculate the supported binary formats for the specified macOS version and architecture."""
    formats = [cpu_arch]
    if cpu_arch == "x86_64":
        if version >= (10, 4):
            formats.extend(["intel", "fat64", "fat32"])
        else:
            return []
    elif cpu_arch == "i386":
        if version >= (10, 4):
            formats.extend(["intel", "fat32", "fat"])
        else:
            return []
    elif cpu_arch == "ppc64":
        if version > (10, 5) or version < (10, 4):
            return []
        else:
            formats.extend("fat64")
    elif cpu_arch == "ppc":
        if version <= (10, 6):
            formats.extend(["fat", "fat32"])
        else:
            return []

    formats.append("universal")
    return formats


def _mac_platforms(version=None, arch=None) -> Sequence[str]:
    """Calculate the platform tags for macOS."""
    version_str, _, cpu_arch = platform.mac_ver()
    if version is None:
        version = tuple(map(int, version_str.split(".")[:2]))
    if arch is None:
        arch = _mac_arch(cpu_arch)
    platforms: List[str] = []
    for minor_version in range(version[1], -1, -1):
        compat_version = version[0], minor_version
        binary_formats = _mac_binary_formats(compat_version, cpu_arch)
        for binary_format in binary_formats:
            platforms.append(
                f"macosx_{compat_version[0]}_{compat_version[1]}_{binary_format}"
            )
    return platforms


def _windows_platforms() -> Sequence[str]:
    # XXX Is this necessary?
    raise NotImplementedError


def _linux_platforms() -> Sequence[str]:
    # XXX 32-bit interpreter on 64-bit Linux
    # XXX manylinux
    raise NotImplementedError


def _generic_platforms() -> Sequence[str]:
    platform = distutils.util.get_platform()
    platform = platform.replace(".", "_").replace("-", "_")
    return [platform]


def _interpreter_name() -> str:
    """Return the name of the running interpreter."""
    name = (
        sys.implementation.name
    )  # XXX: Darn you, Python 2.7! platform.python_implementation()?
    return INTERPRETER_SHORT_NAMES.get(name) or name


def sys_tags() -> Iterable[Tag]:
    """Return the sequence of tag triples for the running interpreter.

    The order of the sequence corresponds to priority order for the interpreter,
    from most to least important.

    """
    py_version = sys.version_info[:2]
    interpreter_name = _interpreter_name()
    if sys.platform == "darwin":
        platforms = _mac_platforms()
    # In Python 3.3 the "linux" platform went from having the major version to not,
    # e.g. "linux3" to just "linux".
    elif sys.platform.startswith("linux"):
        platforms = _linux_platforms()
    else:
        platforms = _generic_platforms()

    if interpreter_name == "cp":
        return _cpython_tags(py_version, platforms)
    elif interpreter_name == "pp":
        return _pypy_tags(py_version, platforms)
    else:
        return _generic_tags(py_version, interpreter_name, platforms)


# XXX Implement _mac_platforms() (and test as we go)
# XXX Test _generic_platforms()
# XXX Implement _generic_tags()
# XXX Implement _cpython_tags()
# XXX test sys_tags()


# XXX https://pypi.org/project/mysql-connector-python/#files
# XXX https://pypi.org/project/pip/#files
# XXX https://pypi.org/project/numpy/#files
