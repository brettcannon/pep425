import platform
from typing import Any, Container, Iterable, List, Sequence, Tuple

from . import _generic


def architecture(arch, *, is_32bit=_generic.IS_32_BIT_INTERPRETER):
    """Calculate the CPU architecture for the interpreter on macOS."""
    if is_32bit:
        if arch.startswith("ppc"):
            return "ppc"
        else:
            return "i386"
    else:
        return arch


def binary_formats(version, cpu_arch: str) -> Sequence[str]:
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


def platforms(version=None, arch=None) -> Sequence[str]:
    """Calculate the platform tags for macOS."""
    version_str, _, cpu_arch = platform.mac_ver()
    if version is None:
        version = tuple(map(int, version_str.split(".")[:2]))
    if arch is None:
        arch = architecture(cpu_arch)
    platforms: List[str] = []
    for minor_version in range(version[1], -1, -1):
        compat_version = version[0], minor_version
        bin_formats = binary_formats(compat_version, cpu_arch)
        for binary_format in bin_formats:
            platforms.append(
                f"macosx_{compat_version[0]}_{compat_version[1]}_{binary_format}"
            )
    return platforms
