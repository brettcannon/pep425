import distutils.util
import enum
import sys
import sysconfig


def sys_tag_set():
    """Return the tag set for the running interpreter."""
    # XXX Detect CPython
    # XXX Detect PyPy


_DISTRO_SHORT_NAMES = {"cpython": "cp", "pypy": "pp", "ironpython": "ip",
                       "jython": "jy"}

class TagSet:
    """A tag set representing an interpreter.

    A tag set is made up of:

    1. Python distribution and version.
    2. ABI compatibility.
    3. Platform/OS.

    """

    def __init__(self, distribution: str = sys.implementation.name,
                 version: str: sysconfig.get_config_var("py_version_nodot"),
                 abi: str = sysconfig.get_config_var("SOABI"),
                 platform: str = distutils.util.get_platform()):
        # XXX Default values based on what the PEP says.
        # XXX Might not provide any defaults and instead provide them through sys_tag_set().
        self.py_version = _DISTRO_SHORT_NAMES.setdefault(distribution) + version
        self.abi = abi
        self.platform = platform

    def __str__(self) -> str:
        return "-".join([self.py_version, self.abi, self.platform])

    def py_versions(self) -> Iterable[str]:
        # XXX Indexable? What type hint is appropriate to work with reversed()?
        return [self.py_version]

    def abis(self) -> Iterable[str]:
        return [self.abi, "none"]

    def platforms(self) -> Iterable[str]:
        return [self.platform, "any"]


class CPythonTagSet(TagSet):

    """A tag set for CPython."""

    def __init__(self, version, abi, platform):
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

    def __init__(self, version, abi, platform):
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


def combinations(tag_set, bottom_pri, middle_pri, top_pri) -> Iterable[TagSet]:
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


    def __init__(self, py_versions: Iterable[str], abis: Iterable[str],
                 platforms: Iterable[str]):
        self.py_versions = list(py_versions)
        self.abis = list(abis)
        self.platforms = list(platforms)

    @classmethod
    def parse(cls, tags: str) -> MultiTagSet:
        """Parse a mulit-value tag set.

        Multiple values for the same tag are separated by ``.``. For example,
        ``cp37-cp37m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64``
        represents CPython 3.7, an ABI of cp37m, and macOS compatibility for
        four different platforms.

        """
        py_versions, abis, platforms = tags.split("-")
        return cls(py_versions.split("."), abis.split("."), platforms.split("."))

    def __contains__(self, tag_set: TagSet) -> Bool:
        """Check if tag_set is compatible."""
        return (tag_set.py_version in self.py_versions
                and tag_set.abi in self.abis
                and tag_set.platform in self.platforms)

# XXX Parse wheel file names (somehow; not sure if that should be in here or another library)
# XXX for tag_set in combinations():
# XXX   if tag-set in wheel_tag_set: return wheel
