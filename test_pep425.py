import distutils.util
import os.path

try:
    import pathlib
except ImportError:
    pathlib = None
import platform
import sys
import sysconfig
import types

import pytest

import pep425


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
    assert repr(example_tag) == "<py3-none-any @ {tag_id}>".format(
        tag_id=id(example_tag)
    )


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
    path = os.path.join("some", "location", "gidgethub-3.0.0-py3-none-any.whl")
    given = pep425.parse_wheel_tag(path)
    assert given == {example_tag}
    if pathlib and sys.version_info[:2] >= (3, 6):
        given = pep425.parse_wheel_tag(
            pathlib.PurePath("some") / "location" / "gidgethub-3.0.0-py3-none-any.whl"
        )
        assert given == {example_tag}


def test_parse_wheel_tag_multi_interpreter(example_tag):
    expected = {example_tag, pep425.Tag("py2", "none", "any")}
    given = pep425.parse_wheel_tag("pip-18.0-py2.py3-none-any.whl")
    assert given == expected


@pytest.mark.parametrize(
    "name,expected",
    [("CPython", "cp"), ("PyPy", "pp"), ("Jython", "jy"), ("IronPython", "ip")],
)
def test__interpreter_name_cpython(name, expected, monkeypatch):
    if platform.python_implementation().lower() != name:
        monkeypatch.setattr(platform, "python_implementation", lambda: name)
    assert pep425._interpreter_name() == expected


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


def test_macOS_version_detection(monkeypatch):
    if platform.system() != "Darwin":
        monkeypatch.setattr(
            platform, "mac_ver", lambda: ("10.14", ("", "", ""), "x86_64")
        )
    version = platform.mac_ver()[0].split(".")
    expected = "macosx_{major}_{minor}".format(major=version[0], minor=version[1])
    platforms = pep425._mac_platforms(arch="x86_64")
    assert platforms[0].startswith(expected)


@pytest.mark.parametrize("arch", ["x86_64", "i386"])
def test_macOS_arch_detection(arch, monkeypatch):
    if platform.system() != "Darwin" or platform.mac_ver()[2] != arch:
        monkeypatch.setattr(platform, "mac_ver", lambda: ("10.14", ("", "", ""), arch))
    assert pep425._mac_platforms((10, 14))[0].endswith(arch)


def test_cpython_abi_py3(monkeypatch):
    if platform.python_implementation() != "CPython" or not sysconfig.get_config_var(
        "SOABI"
    ):
        monkeypatch.setattr(
            sysconfig, "get_config_var", lambda key: "'cpython-37m-darwin'"
        )
    _, soabi, _ = sysconfig.get_config_var("SOABI").split("-", 2)
    assert "cp{soabi}".format(soabi=soabi) == pep425._cpython_abi(sys.version_info[:2])


@pytest.mark.parametrize(
    "debug,pymalloc,unicode_width",
    [
        (False, False, 2),
        (True, False, 2),
        (False, True, 2),
        (False, False, 4),
        (True, True, 2),
        (False, True, 4),
        (True, True, 4),
    ],
)
def test_cpython_abi_py2(debug, pymalloc, unicode_width, monkeypatch):
    if platform.python_implementation() != "CPython" or sysconfig.get_config_var(
        "SOABI"
    ):
        if debug != sysconfig.get_config_var("Py_DEBUG") or pymalloc != sysconfig.get_config_var("WITH_PYMALLOC") or sysconfig.get_config_var("Py_UNICODE_SIZE") != unicode_width:
            config_vars = {"SOABI": None, "Py_DEBUG": int(debug), "WITH_PYMALLOC": int(pymalloc), "Py_UNICODE_SIZE": unicode_width}
            monkeypatch.setattr(sysconfig, "get_config_var", config_vars.__getitem__)
        options = ""
        if debug:
            options += "d"
        if pymalloc:
            options += "m"
        if unicode_width == 4:
            options += "u"
        assert "cp33{}".format(options) == pep425._cpython_abi((3, 3))


def test_independent_tags():
    assert list(pep425._independent_tags("cp33", (3, 3), ["plat1", "plat2"])) == [
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


def test_cpython_tags():
    tags = list(pep425._cpython_tags((3, 3), "cp33", "cp33m", ["plat1", "plat2"]))
    assert tags == [
        pep425.Tag("cp33", "cp33m", "plat1"),
        pep425.Tag("cp33", "cp33m", "plat2"),
        pep425.Tag("cp33", "abi3", "plat1"),
        pep425.Tag("cp33", "abi3", "plat2"),
        pep425.Tag("cp33", "none", "plat1"),
        pep425.Tag("cp33", "none", "plat2"),
        pep425.Tag("cp32", "abi3", "plat1"),
        pep425.Tag("cp32", "abi3", "plat2"),
    ]


def test_sys_tags_on_mac_cpython(monkeypatch):
    if platform.python_implementation() != "CPython":
        monkeypatch.setattr(platform, "python_implementation", lambda: "CPython")
        monkeypatch.setattr(pep425, "_cpython_abi", lambda py_version: "cp33m")
    if platform.system() != "Darwin":
        monkeypatch.setattr(platform, "system", lambda: "Darwin")
        monkeypatch.setattr(pep425, "_mac_platforms", lambda: ["macosx_10_5_x86_64"])
    abi = pep425._cpython_abi(sys.version_info[:2])
    platforms = pep425._mac_platforms()
    tags = list(pep425.sys_tags())
    assert tags[0] == pep425.Tag(
        "cp{major}{minor}".format(major=sys.version_info[0], minor=sys.version_info[1]),
        abi,
        platforms[0],
    )
    assert tags[-1] == pep425.Tag("py{}0".format(sys.version_info[0]), "none", "any")


def test_generic_abi():
    abi = sysconfig.get_config_var("SOABI")
    if abi:
        abi = abi.replace(".", "_").replace("-", "_")
    else:
        abi = "none"
    assert abi == pep425._generic_abi()


def test_pypy_tags(monkeypatch):
    if platform.python_implementation() != "PyPy":
        monkeypatch.setattr(platform, "python_implementation", lambda: "PyPy")
        monkeypatch.setattr(pep425, "_pypy_interpreter", lambda: "pp360")
    interpreter = pep425._pypy_interpreter()
    tags = list(pep425._pypy_tags((3, 3), interpreter, "pypy3_60", ["plat1", "plat2"]))
    assert tags == [
        pep425.Tag(interpreter, "pypy3_60", "plat1"),
        pep425.Tag(interpreter, "pypy3_60", "plat2"),
        pep425.Tag(interpreter, "none", "plat1"),
        pep425.Tag(interpreter, "none", "plat2"),
    ]


def test_sys_tags_on_mac_pypy(monkeypatch):
    if platform.python_implementation() != "PyPy":
        monkeypatch.setattr(platform, "python_implementation", lambda: "PyPy")
        monkeypatch.setattr(pep425, "_pypy_interpreter", lambda: "pp360")
    if platform.system() != "Darwin":
        monkeypatch.setattr(platform, "system", lambda: "Darwin")
        monkeypatch.setattr(pep425, "_mac_platforms", lambda: ["macosx_10_5_x86_64"])
    interpreter = pep425._pypy_interpreter()
    abi = pep425._generic_abi()
    platforms = pep425._mac_platforms()
    tags = list(pep425.sys_tags())
    assert tags[0] == pep425.Tag(interpreter, abi, platforms[0])
    assert tags[-1] == pep425.Tag("py{}0".format(sys.version_info[0]), "none", "any")


def test_generic_interpreter():
    version = sysconfig.get_config_var("py_version_nodot")
    if not version:
        version = "".join(sys.version_info[:2])
    assert "sillywalk{version}".format(version=version) == pep425._generic_interpreter(
        "sillywalk", sys.version_info[:2]
    )


def test_generic_platforms():
    platform = distutils.util.get_platform().replace("-", "_").replace(".", "_")
    assert pep425._generic_platforms() == [platform]


def test_generic_tags():
    tags = list(pep425._generic_tags("sillywalk33", (3, 3), "abi", ["plat1", "plat2"]))
    assert tags == [
        pep425.Tag("sillywalk33", "abi", "plat1"),
        pep425.Tag("sillywalk33", "abi", "plat2"),
        pep425.Tag("sillywalk33", "none", "plat1"),
        pep425.Tag("sillywalk33", "none", "plat2"),
    ]


def test_sys_tags_on_windows_cpython(monkeypatch):
    if platform.python_implementation() != "CPython":
        monkeypatch.setattr(platform, "python_implementation", lambda: "CPython")
        monkeypatch.setattr(pep425, "_cpython_abi", lambda py_version: "cp33m")
    if platform.system() != "Windows":
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.setattr(pep425, "_generic_platforms", lambda: ["win_amd64"])
    abi = pep425._cpython_abi(sys.version_info[:2])
    platforms = pep425._generic_platforms()
    tags = list(pep425.sys_tags())
    assert tags[0] == pep425.Tag(
        "cp{major}{minor}".format(major=sys.version_info[0], minor=sys.version_info[1]),
        abi,
        platforms[0],
    )
    assert tags[-1] == pep425.Tag("py{}0".format(sys.version_info[0]), "none", "any")


def test_is_manylinux_compatible_module_support(monkeypatch):
    monkeypatch.setattr(pep425, "_have_compatible_glibc", lambda *args: False)
    module_name = "_manylinux"
    module = types.ModuleType(module_name)
    module.manylinux1_compatible = True
    monkeypatch.setitem(sys.modules, module_name, module)
    assert pep425._is_manylinux_compatible("manylinux1", (2, 5))
    module.manylinux1_compatible = False
    assert not pep425._is_manylinux_compatible("manylinux1", (2, 5))
    del module.manylinux1_compatible
    assert not pep425._is_manylinux_compatible("manylinux1", (2, 5))
    monkeypatch.setitem(sys.modules, module_name, None)
    assert not pep425._is_manylinux_compatible("manylinux1", (2, 5))


def test_is_manylinux_compatible_glibc_support(monkeypatch):
    monkeypatch.setitem(sys.modules, "_manylinux", None)
    monkeypatch.setattr(pep425, "_have_compatible_glibc", lambda major, minor: (major, minor) <= (2, 5))
    assert pep425._have_compatible_glibc(2, 0)
    assert pep425._have_compatible_glibc(2, 5)
    assert not pep425._have_compatible_glibc(2, 10)


@pytest.mark.skipif(platform.system() != "Linux", reason="requires Linux/glibc")
def test_have_compatible_glibc():
    # Assuming no one is running this test with a version of glibc released in 1997.
    assert pep425._have_compatible_glibc(2, 0)


def test_linux_platforms_64bit_on_64bit(monkeypatch):
    if platform.system() != "Linux" or distutils.util.get_platform().endswith("_x86_64"):
        monkeypatch.setattr(distutils.util, "get_platform", lambda: "linux_x86_64")
        monkeypatch.setattr(pep425, "_is_manylinux_compatbible", lambda *args: False)
    linux_platform = pep425._linux_platforms(is_32bit=False)[-1]
    assert linux_platform == "linux_x86_64"


def test_linux_platforms_32bit_linux_on_64bit_OS():
    if platform.system() != "Linux" or distutils.util.get_platform().endswith("_i686"):
        monkeypatch.setattr(distutils.util, "get_platform", lambda: "linux_i686")
        monkeypatch.setattr(pep425, "_is_manylinux_compatbible", lambda *args: False)
    linux_platform = pep425._linux_platforms(is_32bit=True)[-1]
    assert linux_platform == "linux_i686"


def test_linux_platforms_manylinux1(monkeypatch):
    monkeypatch.setattr(pep425, "_is_manylinux_compatible", lambda name, _: name == "manylinux1")
    if platform.system() != "Linux":
        monkeypatch.setattr(distutils.util, "get_platform", lambda: "linux_x86_64")
    platforms = pep425._linux_platforms(is_32bit=False)
    assert platforms == ["manylinux1_x86_64", "linux_x86_64"]


def test_linux_platforms_manylinux2010(monkeypatch):
    monkeypatch.setattr(pep425, "_is_manylinux_compatible", lambda name, _: name == "manylinux2010")
    if platform.system() != "Linux":
        monkeypatch.setattr(distutils.util, "get_platform", lambda: "linux_x86_64")
    platforms = pep425._linux_platforms(is_32bit=False)
    assert platforms == ["manylinux2010_x86_64", "manylinux1_x86_64", "linux_x86_64"]


def test_sys_tags_linux_cpython(monkeypatch):
    if platform.python_implementation() != "CPython":
        monkeypatch.setattr(platform, "python_implementation", lambda: "CPython")
        monkeypatch.setattr(pep425, "_cpython_abi", lambda py_version: "cp33m")
    if platform.system() != "Linux":
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.setattr(pep425, "_linux_platforms", lambda: ["linux_x86_64"])
    abi = pep425._cpython_abi(sys.version_info[:2])
    platforms = pep425._linux_platforms()
    tags = list(pep425.sys_tags())
    assert tags[0] == pep425.Tag(
        "cp{major}{minor}".format(major=sys.version_info[0], minor=sys.version_info[1]),
        abi,
        platforms[0],
    )
    assert tags[-1] == pep425.Tag("py{}0".format(sys.version_info[0]), "none", "any")
