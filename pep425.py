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


class TagSet:
    """A tag set representing an interpreter.

    A tag set is made up of:

    1. Python distribution and version.
    2. ABI compatibility.
    3. Platform/OS.

    """

    def __init__(
        self,
        distribution: str,
        no_dot_version: str,
        abi: str = "none",
        platform: str = "any",
    ) -> None:
        self._distro = distribution
        self._version = no_dot_version
        self.py_version = (
            _DISTRO_SHORT_NAMES.get(distribution, distribution) + no_dot_version
        )
        self.abi = abi
        self.platform = platform

    def __str__(self) -> str:
        return "-".join([self.py_version, self.abi, self.platform])

    def py_versions(self) -> List[str]:
        major = self._version[0]
        minor = self._version[1:]
        distros = _options_list(self._distro, "py")
        combinations = []
        for distro in distros:
            if minor:
                combinations.append(f"{distro}{major}{minor}")
            combinations.append(f"{distro}{major}")
        return combinations

    def abis(self) -> List[str]:
        return _options_list(self.abi, "none")

    def platforms(self) -> List[str]:
        return _options_list(self.platform, "any")


class CPythonTagSet(TagSet):

    """A tag set for CPython."""

    def __init__(self, version, abi, platform) -> None:
        # XXX Provide appropriate defaults.
        super().__init__(_DISTRO_SHORT_NAMES["cpython"], version, abi, platform)

    def py_versions(self) -> List[str]:
        """Go from major + version to major, CPython to 'py'."""
        # XXX Make sure to start from the proper position if a less specific
        #     version is provided.

    def abis(self) -> List[str]:
        """Go from ABI to 'abi3' to 'XXX'."""
        # XXX Make sure to start from proper position when given a less specific
        #     version.

    # XXX manylinux?


class PyPyTagSet(TagSet):

    """A tag set for PyPy3."""

    def __init__(self, version, abi, platform) -> None:
        # XXX Provide appropriate defaults.
        super().__init__(_DISTRO_SHORT_NAMES["pypy"], version, abi, platform)


@enum.unique
class TagType(enum.Enum):
    """Possible tags.

    Each value corresponds to an attribute on TagSet.

    """

    py_version = "py_version"
    abi = "abi"
    platform = "platform"


def combinations(
    tag_set, bottom_pri, middle_pri, top_pri
) -> Generator[TagSet, None, None]:
    """Create an iterable of tag sets.

    The parameters bottom_pri, middle_pri, and top_pri represent the bottom,
    middle, and top priority out of the three tags contained in a tag set.
    The bottom priority will mutate the most while the top priority will mutate
    the least.

    """
    # XXX Check what pip's defaults are to choose a default.
    # XXX Yield tag sets


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

    def __contains__(self, tag_set: TagSet) -> bool:
        """Check if tag_set is compatible."""
        return (
            tag_set.py_version in self.py_versions
            and tag_set.abi in self.abis
            and tag_set.platform in self.platforms
        )


# XXX Parse wheel file names (somehow; not sure if that should be in here or another library)
# XXX for tag_set in combinations():
# XXX   if tag-set in wheel_tag_set: return wheel
