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
