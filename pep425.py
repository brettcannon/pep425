"""Provide support for PEP 425 compatibility tags triples."""

import distutils.util
import os
import pathlib
import platform
import sys
import sysconfig


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

    def __init__(self, interpreter, abi, platform):
        """Initialize the instance attributes.

        All values are lowercased.

        """
        self._tags = interpreter.lower(), abi.lower(), platform.lower()

    def __eq__(self, other):
        return self._tags == other._tags

    def __hash__(self):
        return hash(self._tags)

    def __str__(self):
        return "-".join(self._tags)

    def __repr__(self):
        return f"<{self} @ {id(self)}>"

    @property
    def interpreter(self):
        return self._tags[0]

    @property
    def abi(self):
        return self._tags[1]

    @property
    def platform(self):
        return self._tags[2]


def parse_tag(tag: str):
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


def parse_wheel_tag(path):
    """Parse the path of a wheel file for its tag triple(s)."""
    name = pathlib.PurePath(path).stem
    parts = 3
    index = len(name)
    while parts:
        index = name.rindex("-", 0, index)
        parts -= 1
    return parse_tag(name[index + 1 :])


def _cpython_abi():
    """Calcuate the ABI for this CPython interpreter."""
    soabi = sysconfig.get_config_var("SOABI")
    if soabi:
        _, options, _ = soabi.split("-")
        return f"cp{options}"
    else:
        # XXX Python 2.7.
        raise NotImplementedError


def _cpython_tags(py_version, abi, platforms):
    platforms = list(platforms)  # Iterating multiple times, so make concrete.
    # TODO: Is using py_version_nodot for interpreter version critical?
    interpreter = f"cp{py_version[0]}{py_version[1]}"
    yield from (Tag(interpreter, abi, platform) for platform in platforms)
    yield from (Tag(interpreter, "abi3", platform) for platform in platforms)
    yield from (Tag(interpreter, "none", platform) for platform in platforms)
    # PEP 384 was first implemented in Python 3.2.
    for minor_version in range(py_version[1] - 1, 1, -1):
        for platform in platforms:
            yield Tag(f"cp{py_version[0]}{minor_version}", "abi3", platform)
    yield from _independent_tags(interpreter, py_version, platforms)


def _pypy_tags(py_version, platforms):
    interpreter_version = (
        f"{py_version[0]}{sys.pypy_version_info.major}{sys.pypy_version_info.minor}"
    )
    interpreter = f"pp{interpreter_version}"
    # XXX
    raise NotImplementedError


def _generic_tags(py_version, interpreter_name, platforms):
    interpreter_version = sysconfig.get_config_var("py_version_nodot")
    if not interpreter_version:
        interpreter_version = "".join(py_version)
    interpreter = f"{interpreter_name}{interpreter_version}"
    # XXX ABI
    # XXX
    raise NotImplementedError


def _py_interpreter_range(py_version):
    """Yield Python versions in descending order.

    After the latest version, the major-only version will be yielded, and then
    all following versions up to 'end'.

    """
    yield f"py{py_version[0]}{py_version[1]}"
    yield f"py{py_version[0]}"
    for minor in range(py_version[1] - 1, -1, -1):
        yield f"py{py_version[0]}{minor}"


def _independent_tags(interpreter, py_version, platforms):
    """Return the sequence of tags that are consistent across implementations."""
    for version in _py_interpreter_range(py_version):
        for platform in platforms:
            yield Tag(version, "none", platform)
    yield Tag(interpreter, "none", "any")
    for version in _py_interpreter_range(py_version):
        yield Tag(version, "none", "any")


def _mac_arch(arch, *, is_32bit=_32_BIT_INTERPRETER):
    """Calculate the CPU architecture for the interpreter on macOS."""
    if is_32bit:
        if arch.startswith("ppc"):
            return "ppc"
        else:
            return "i386"
    else:
        return arch


def _mac_binary_formats(version, cpu_arch: str):
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
        # TODO: Need to care about 32-bit PPC for ppc64 through 10.2?
        if version > (10, 5) or version < (10, 4):
            return []
        else:
            formats.append("fat64")
    elif cpu_arch == "ppc":
        if version <= (10, 6):
            formats.extend(["fat32", "fat"])
        else:
            return []

    formats.append("universal")
    return formats


def _mac_platforms(version=None, arch=None):
    """Calculate the platform tags for macOS."""
    version_str, _, cpu_arch = platform.mac_ver()
    if version is None:
        version = tuple(map(int, version_str.split(".")[:2]))
    if arch is None:
        arch = _mac_arch(cpu_arch)
    platforms = []
    for minor_version in range(version[1], -1, -1):
        compat_version = version[0], minor_version
        binary_formats = _mac_binary_formats(compat_version, cpu_arch)
        for binary_format in binary_formats:
            platforms.append(
                f"macosx_{compat_version[0]}_{compat_version[1]}_{binary_format}"
            )
    return platforms


def _windows_platforms():
    # XXX Is this function even necessary?
    raise NotImplementedError


def _linux_platforms():
    # XXX 32-bit interpreter on 64-bit Linux
    # XXX manylinux
    raise NotImplementedError


def _generic_platforms():
    platform = distutils.util.get_platform()
    platform = platform.replace(".", "_").replace("-", "_")
    return [platform]


def _interpreter_name():
    """Return the name of the running interpreter."""
    # XXX: Darn you, Python 2.7! platform.python_implementation()?
    name = sys.implementation.name
    return INTERPRETER_SHORT_NAMES.get(name) or name


def sys_tags():
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
        abi = _cpython_abi()
        return _cpython_tags(py_version, abi, platforms)
    elif interpreter_name == "pp":
        return _pypy_tags(py_version, platforms)
    else:
        return _generic_tags(py_version, interpreter_name, platforms)


# XXX Implement tags for PyPy
# XXX Test _generic_platforms()
# XXX Implement _generic_tags()


# XXX https://pypi.org/project/mysql-connector-python/#files
# XXX https://pypi.org/project/pip/#files
# XXX https://pypi.org/project/numpy/#files
