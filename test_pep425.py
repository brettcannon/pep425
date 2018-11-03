import distutils.util
import pathlib
import platform
import sys
import sysconfig

import pytest

import pep425


def cpython_only(func):
    """Skip 'func' if not running under CPython."""
    return pytest.mark.skipif(
        sys.implementation.name != "cpython", reason="requires CPython"
    )(func)


def pypy_only(func):
    """Skip 'func' if not running under PyPy."""
    return pytest.mark.skipif(
        not hasattr(sys, "pypy_version_info"), reason="requires PyPy"
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


def test_Tag_repr(example_tag):
    assert repr(example_tag) == f"<py3-none-any @ {id(example_tag)}>"


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


@cpython_only
@pytest.mark.skipif(
    not sysconfig.get_config_var("SOABI"), reason="requires SOABI configuration info"
)
def test_cpython_abi():
    _, soabi, _ = sysconfig.get_config_var("SOABI").split("-")
    assert f"cp{soabi}" == pep425._cpython_abi()


def test_cpython_tags():
    tags = list(pep425._cpython_tags((3, 3), "cp33m", ["plat1", "plat2"]))
    assert tags == [
        pep425.Tag("cp33", "cp33m", "plat1"),
        pep425.Tag("cp33", "cp33m", "plat2"),
        pep425.Tag("cp33", "abi3", "plat1"),
        pep425.Tag("cp33", "abi3", "plat2"),
        pep425.Tag("cp33", "none", "plat1"),
        pep425.Tag("cp33", "none", "plat2"),
        pep425.Tag("cp32", "abi3", "plat1"),
        pep425.Tag("cp32", "abi3", "plat2"),
        pep425.Tag("py33", "none", "plat1"),
        pep425.Tag("py33", "none", "plat2"),
        pep425.Tag("py3", "none", "plat1"),
        pep425.Tag("py3", "none", "plat2"),
        pep425.Tag("py32", "none", "plat1"),
        pep425.Tag("py32", "none", "plat2"),
        pep425.Tag("py31", "none", "plat1"),
        pep425.Tag("py31", "none", "plat2"),
        pep425.Tag("py30", "none", "plat1"),
        pep425.Tag("py30", "none", "plat2"),
        pep425.Tag("cp33", "none", "any"),
        pep425.Tag("py33", "none", "any"),
        pep425.Tag("py3", "none", "any"),
        pep425.Tag("py32", "none", "any"),
        pep425.Tag("py31", "none", "any"),
        pep425.Tag("py30", "none", "any"),
    ]


@cpython_only
@mac_only
def test_sys_tags_on_mac_cpython():
    abi = pep425._cpython_abi()
    platforms = pep425._mac_platforms()
    tags = list(pep425.sys_tags())
    assert tags[0] == pep425.Tag(
        f"cp{sys.version_info[0]}{sys.version_info[1]}", abi, platforms[0]
    )
    assert tags[-1] == pep425.Tag("py30", "none", "any")


def test_generic_abi():
    abi = sysconfig.get_config_var("SOABI")
    if abi:
        abi = abi.replace(".", "_").replace("-", "_")
    else:
        abi = "none"
    assert abi == pep425._generic_abi()


@pypy_only
def test_pypy_tags():
    interpreter = pep425._pypy_interpreter()
    tags = list(pep425._pypy_tags((3, 3), "pypy3_60", ["plat1", "plat2"]))
    assert tags == [
        pep425.Tag(interpreter, "pypy3_60", "plat1"),
        pep425.Tag(interpreter, "pypy3_60", "plat2"),
        pep425.Tag(interpreter, "none", "plat1"),
        pep425.Tag(interpreter, "none", "plat2"),
        pep425.Tag("py33", "none", "plat1"),
        pep425.Tag("py33", "none", "plat2"),
        pep425.Tag("py3", "none", "plat1"),
        pep425.Tag("py3", "none", "plat2"),
        pep425.Tag("py32", "none", "plat1"),
        pep425.Tag("py32", "none", "plat2"),
        pep425.Tag("py31", "none", "plat1"),
        pep425.Tag("py31", "none", "plat2"),
        pep425.Tag("py30", "none", "plat1"),
        pep425.Tag("py30", "none", "plat2"),
        pep425.Tag(interpreter, "none", "any"),
        pep425.Tag("py33", "none", "any"),
        pep425.Tag("py3", "none", "any"),
        pep425.Tag("py32", "none", "any"),
        pep425.Tag("py31", "none", "any"),
        pep425.Tag("py30", "none", "any"),
    ]


@pypy_only
@mac_only
def test_sys_tags_on_mac_pypy():
    interpreter = pep425._pypy_interpreter()
    abi = pep425._generic_abi()
    platforms = pep425._mac_platforms()
    tags = list(pep425.sys_tags())
    assert tags[0] == pep425.Tag(interpreter, abi, platforms[0])
    assert tags[-1] == pep425.Tag("py30", "none", "any")


def test_generic_interpreter():
    version = sysconfig.get_config_var("py_version_nodot")
    if not version:
        version = "".join(sys.version_info[:2])
    assert f"sillywalk{version}" == pep425._generic_interpreter(
        "sillywalk", sys.version_info[:2]
    )


def test_generic_platform():
    platform = distutils.util.get_platform().replace("-", "_").replace(".", "_")
    assert pep425._generic_platforms() == [platform]


def test_generic_tags():
    tags = list(pep425._generic_tags("sillywalk33", (3, 3), "abi", ["plat1", "plat2"]))
    assert tags == [
        pep425.Tag("sillywalk33", "abi", "plat1"),
        pep425.Tag("sillywalk33", "abi", "plat2"),
        pep425.Tag("sillywalk33", "none", "plat1"),
        pep425.Tag("sillywalk33", "none", "plat2"),
        pep425.Tag("py33", "none", "plat1"),
        pep425.Tag("py33", "none", "plat2"),
        pep425.Tag("py3", "none", "plat1"),
        pep425.Tag("py3", "none", "plat2"),
        pep425.Tag("py32", "none", "plat1"),
        pep425.Tag("py32", "none", "plat2"),
        pep425.Tag("py31", "none", "plat1"),
        pep425.Tag("py31", "none", "plat2"),
        pep425.Tag("py30", "none", "plat1"),
        pep425.Tag("py30", "none", "plat2"),
        pep425.Tag("sillywalk33", "none", "any"),
        pep425.Tag("py33", "none", "any"),
        pep425.Tag("py3", "none", "any"),
        pep425.Tag("py32", "none", "any"),
        pep425.Tag("py31", "none", "any"),
        pep425.Tag("py30", "none", "any"),
    ]
