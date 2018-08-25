from __future__ import annotations
import distutils.util
import enum
import sys
import sysconfig
from typing import Generator, Iterable, List


_DISTRO_SHORT_NAMES = {
    "python": "py",  # Generic/agnostic.
    "cpython": "cp",
    "pypy": "pp",
    "ironpython": "ip",
    "jython": "jy",
}


def _options_list(specific: str, generic: str) -> List[str]:
    """Build a list that at minimum contains 'generic', at most 'specific'.

    No duplicates will be in the resulting list.

    """
    if specific != generic:
        return [specific, generic]
    else:
        return [generic]


def sys_tag_set():
    """Return the tag set for the running interpreter."""
    # XXX Detect CPython
    # XXX Detect PyPy
    # XXX distribution: str = sys.implementation.name,
    # XXX version: str = sysconfig.get_config_var("py_version_nodot"),
    # XXX abi: str = sysconfig.get_config_var("SOABI"),
    # XXX platform: str = distutils.util.get_platform()


class BaseTagSet:
    """A tag set representing an interpreter.

    A tag set is made up of:

    1. Python distribution and version.
    2. ABI compatibility.
    3. Platform/OS.

    """

    def __init__(self, py_version, abi, platform):
        self.py_version = py_version.lower()
        self.abi = abi.lower()
        self.platform = platform.lower()

    def __str__(self) -> str:
        return "-".join([self.py_version, self.abi, self.platform])


class TagSet(BaseTagSet):
    """A tag set which understands what other tags it supports."""

    def __init__(
        self, distribution: str, version: str, abi: str = "none", platform: str = "any"
    ) -> None:
        self._distro = distribution.lower()
        self._version = version.lower()
        py_version = _DISTRO_SHORT_NAMES.get(self._distro, self._distro) + self._version
        super().__init__(py_version, abi, platform)

    def supported_py_versions(self) -> List[str]:
        """Calculate the supported Python versions."""
        return [self.py_version]

    def supported_abis(self) -> List[str]:
        """Calculate the supported ABIs.

        If not set as the  ABI, 'none' is used as the most generic value.

        """
        return _options_list(self.abi, "none")

    def supported_platforms(self) -> List[str]:
        """Calculate the supported platforms.

        If not set as the platform, 'any' is used as the most generic value.

        """
        return _options_list(self.platform, "any")


class CPythonTagSet(TagSet):

    """A tag set for CPython."""

    def __init__(self, version, abi="none", platform="any") -> None:
        """Create a tag set for CPython.

        The `version` argument is expected to represent the major and minor Python
        version supported by the interpreter with no separator between the
        two numbers. The major version is assumed to be the first digit in the
        string.

        """
        super().__init__(_DISTRO_SHORT_NAMES["cpython"], version, abi, platform)

    def supported_py_versions(self) -> List[str]:
        """Calculate the supported Python versions.

        The supported Python versions go through the specified distribution and
        'py' (as the generic value), first choosing the major/minor version and
        then major-only. E.g. for CPython 3.7, the result is
        ["cpy37", "cp3", "py37", "py3"].

        """
        # According to PEP 425, Python version support is context-sensitive
        # based on whether any ABI or platform has been specified (i.e.
        # ``*-none-any`` versus anything else). Based on a query against PyPI
        # download data on 2018-08-24, there are exactly four projects where
        # the context-sensitivity would come into play and they all provide
        # multiple wheels to cover appropriate versions of Python. Hence it is
        # not considered important enough to complicate the support here for
        # context-sensitive Python version possibilities.
        major = self._version[0]
        minor = self._version[1:]
        distros = _options_list(self._distro, "py")
        combinations = []
        for distro in distros:
            if minor:
                combinations.append(f"{distro}{major}{minor}")
            combinations.append(f"{distro}{major}")
        return combinations

    def supported_abis(self) -> List[str]:
        """Go from ABI to 'abi3' to 'XXX'."""
        # XXX Make sure to start from proper position when given a less specific
        #     version.

    # XXX manylinux?


def combinations(tag_set: TagSet) -> Generator[BaseTagSet, None, None]:
    """Create an iterable of BaseTagSet instances.

    The Python version mutates the fastest, followed by ABI, and then finally
    platform.
    """
    for platform in tag_set.supported_platforms():
        for abi in tag_set.supported_abis():
            for py_version in tag_set.supported_py_versions():
                yield BaseTagSet(py_version, abi, platform)


class MultiValueTagSet:

    """Represent a tag set which has multiple values per tag."""

    def __init__(
        self, py_versions: Iterable[str], abis: Iterable[str], platforms: Iterable[str]
    ) -> None:
        self.py_versions = list(py_versions)
        self.abis = list(abis)
        self.platforms = list(platforms)

    @classmethod
    def parse(cls, tags: str) -> MultiValueTagSet:
        """Parse a mulit-value tag set.

        Multiple values for the same tag are separated by ``.``. For example,
        ``cp37-cp37m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64``
        represents CPython 3.7, an ABI of cp37m, and macOS compatibility for
        four different platforms.

        """
        py_versions, abis, platforms = tags.split("-")
        return cls(py_versions.split("."), abis.split("."), platforms.split("."))

    def __contains__(self, tag_set: BaseTagSet) -> bool:
        """Check if tag_set is compatible."""
        return (
            tag_set.py_version in self.py_versions
            and tag_set.abi in self.abis
            and tag_set.platform in self.platforms
        )


# XXX Parse wheel file names (somehow; not sure if that should be in here or another library)
# XXX for tag_set in combinations():
# XXX   for wheel_tag_set in wheel_tag_sets:
# XXX     if tag_set in wheel_tag_set: return wheel
