import pathlib
import platform
import sys

import pytest

import pep425


def cpython_only(func):
    """Skip 'func' if not running under CPython."""
    return pytest.mark.skipif(
        sys.implementation.name != "cpython", reason="requires CPython"
    )(func)


def mac_only(func):
    """Skip 'func' if not running on macOS."""
    return pytest.mark.skipif(sys.platform != "darwin", reason="requires macOS")(func)


def arch_64_only(func):
    """Skip 'func' if not running on a 64-bit interpreter."""
    return pytest.mark.skipif(
        sys.maxsize <= 2 ** 32, reason="requires a 64-bit interpreter"
    )(func)


@pytest.fixture
def example_tag():
    return pep425.Tag("py3", "none", "any")


def test_Tag_lowercasing():
    tag = pep425.Tag("PY3", "None", "ANY")
    assert tag.interpreter == "py3"
    assert tag.abi == "none"
    assert tag.platform == "any"


def test_Tag_equality():
    args = "py3", "none", "any"
    assert pep425.Tag(*args) == pep425.Tag(*args)


def test_Tag_hashing(example_tag):
    tags = {example_tag}  # Should not raise TypeError.


def test_Tag_str(example_tag):
    assert str(example_tag) == "py3-none-any"


def test_Tag_attribute_access(example_tag):
    assert example_tag.interpreter == "py3"
    assert example_tag.abi == "none"
    assert example_tag.platform == "any"


def test_parse_tag_simple(example_tag):
    tags = pep425.parse_tag(str(example_tag))
    assert tags == {example_tag}


def test_parse_tag_multi_interpreter(example_tag):
    expected = {example_tag, pep425.Tag("py2", "none", "any")}
    given = pep425.parse_tag("py2.py3-none-any")
    assert given == expected


def test_parse_tag_multi_platform():
    expected = {
        pep425.Tag("cp37", "cp37m", platform)
        for platform in (
            "macosx_10_6_intel",
            "macosx_10_9_intel",
            "macosx_10_9_x86_64",
            "macosx_10_10_intel",
            "macosx_10_10_x86_64",
        )
    }
    given = pep425.parse_tag(
        "cp37-cp37m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64"
    )
    assert given == expected


def test_parse_wheel_tag_simple(example_tag):
    given = pep425.parse_wheel_tag("gidgethub-3.0.0-py3-none-any.whl")
    assert given == {example_tag}


def test_parse_wheel_tag_path(example_tag):
    given = pep425.parse_wheel_tag(
        pathlib.PurePath("some") / "location" / "gidgethub-3.0.0-py3-none-any.whl"
    )
    assert given == {example_tag}


def test_parse_wheel_tag_multi_interpreter(example_tag):
    expected = {example_tag, pep425.Tag("py2", "none", "any")}
    given = pep425.parse_wheel_tag("pip-18.0-py2.py3-none-any.whl")
    assert given == expected


@cpython_only
def test__interpreter_name_cpython():
    assert pep425._interpreter_name() == "cp"


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
    assert pep425._mac_arch(arch, is_32bit=is_32bit) == expected


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
    assert pep425._mac_binary_formats(version, arch) == expected


def test_mac_platforms():
    platforms = pep425._mac_platforms((10, 5), "x86_64")
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

    assert len(pep425._mac_platforms((10, 17), "x86_64")) == 14 * 5

    assert not pep425._mac_platforms((10, 0), "x86_64")


@mac_only
def test_macOS_version_detection():
    version = platform.mac_ver()[0].split(".")
    expected = f"macosx_{version[0]}_{version[1]}"
    platforms = pep425._mac_platforms(arch="x86_64")
    assert platforms[0].startswith(expected)


@mac_only
@arch_64_only
def test_macOS_arch_detection():
    arch = platform.mac_ver()[2]
    assert pep425._mac_platforms((10, 17))[0].endswith(arch)
