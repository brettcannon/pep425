import sysconfig

import pep425


def test_defaults():
    tag_set = pep425.TagSet("py", "40")
    assert tag_set.py_version == "py40"
    assert tag_set.abi == "none"
    assert tag_set.platform == "any"
    assert tag_set.py_versions() == ["py40", "py4"]
    assert tag_set.abis() == ["none"]
    assert tag_set.platforms() == ["any"]


def test_short_name():
    tag_set = pep425.TagSet("jython", "27")
    assert tag_set.py_version == "jy27"


def test_combinations():
    tag_set = pep425.TagSet("swallow", "37", "cp37m", "manylinux")
    assert tag_set.py_versions() == ["swallow37", "swallow3", "py37", "py3"]
    assert tag_set.abis() == ["cp37m", "none"]
    assert tag_set.platforms() == ["manylinux", "any"]


def test___str__():
    tag_set = pep425.TagSet("gilectomy", "35", "cp35m", "manylinux")
    assert str(tag_set) == "gilectomy35-cp35m-manylinux"
