import platform
import sys

import pytest

import pep425._mac

import test_pep425


def mac_only(func):
    """Skip 'func' if not running on macOS."""
    return pytest.mark.skipif(sys.platform != "darwin", reason="requires macOS")(func)


@pytest.mark.parametrize(
    "arch, is_32bit, expected",
    [
        ("i386", True, "i386"),
        ("ppc", True, "ppc"),
        ("x86_64", False, "x86_64"),
        ("x86_64", True, "i386"),
        ("ppc64", False, "ppc64"),
        ("ppc64", True, "ppc"),
    ],
)
def test_macOS_architectures(arch, is_32bit, expected):
    assert pep425._mac.architecture(arch, is_32bit=is_32bit) == expected


@pytest.mark.parametrize(
    "version,arch,expected",
    [
        ((10, 17), "x86_64", ["x86_64", "intel", "fat64", "fat32", "universal"]),
        ((10, 4), "x86_64", ["x86_64", "intel", "fat64", "fat32", "universal"]),
        ((10, 3), "x86_64", []),
        ((10, 17), "i386", ["i386", "intel", "fat32", "fat", "universal"]),
        ((10, 4), "i386", ["i386", "intel", "fat32", "fat", "universal"]),
        ((10, 3), "i386", []),
        ((10, 17), "ppc64", []),
        ((10, 6), "ppc64", []),
        ((10, 5), "ppc64", ["ppc64", "fat64", "universal"]),
        ((10, 3), "ppc64", []),
        ((10, 17), "ppc", []),
        ((10, 7), "ppc", []),
        ((10, 6), "ppc", ["ppc", "fat32", "fat", "universal"]),
        ((10, 0), "ppc", ["ppc", "fat32", "fat", "universal"]),
    ],
)
def test_macOS_binary_formats(version, arch, expected):
    assert pep425._mac.binary_formats(version, arch) == expected


def test_mac_platforms():
    platforms = pep425._mac.platforms((10, 5), "x86_64")
    assert platforms == [
        "macosx_10_5_x86_64",
        "macosx_10_5_intel",
        "macosx_10_5_fat64",
        "macosx_10_5_fat32",
        "macosx_10_5_universal",
        "macosx_10_4_x86_64",
        "macosx_10_4_intel",
        "macosx_10_4_fat64",
        "macosx_10_4_fat32",
        "macosx_10_4_universal",
    ]

    assert len(pep425._mac.platforms((10, 17), "x86_64")) == 14 * 5

    assert not pep425._mac.platforms((10, 0), "x86_64")


@mac_only
def test_macOS_version_detection():
    version = platform.mac_ver()[0].split(".")
    expected = f"macosx_{version[0]}_{version[1]}"
    platforms = pep425._mac.platforms(arch="x86_64")
    assert platforms[0].startswith(expected)


@mac_only
@test_pep425.arch_64_only
def test_macOS_arch_detection():
    arch = platform.mac_ver()[2]
    assert pep425._mac.platforms((10, 17))[0].endswith(arch)
