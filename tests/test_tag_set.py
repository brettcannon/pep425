import pep425


def test_lowercasing():
    tag_set = pep425.BaseTagSet("Hello37", "Abi", "Plat")
    assert tag_set.py_version == "hello37"
    assert tag_set.abi == "abi"
    assert tag_set.platform == "plat"


def test___str__():
    tag_set = pep425.BaseTagSet("gilectomy35", "cp35m", "manylinux")
    assert str(tag_set) == "gilectomy35-cp35m-manylinux"


def test_defaults():
    tag_set = pep425.TagSet("unladen", "40")
    assert tag_set.py_version == "unladen40"
    assert tag_set.abi == "none"
    assert tag_set.platform == "any"
    assert tag_set.supported_py_versions() == ["unladen40"]
    assert tag_set.supported_abis() == ["none"]
    assert tag_set.supported_platforms() == ["any"]


def test_short_name():
    tag_set = pep425.TagSet("jython", "27")
    assert tag_set.py_version == "jy27"


def test_cpython_defaults():
    tag_set = pep425.CPythonTagSet("37")
    assert tag_set.py_version == "cp37"
    assert tag_set.abi == "none"
    assert tag_set.platform == "any"


def test_cpython_supported_versions():
    tag_set = pep425.CPythonTagSet("37", "cp37m", "minix3_x64")
    assert tag_set.supported_py_versions() == ["cp37", "cp3", "py37", "py3"]


def test_cpython_abi_possibilities():
    tag_set = pep425.CPythonTagSet("37", "cp37m", "minix3_x64")
    assert tag_set.supported_abis() == ["cp37m", "abi3", "none"]
    tag_set = pep425.CPythonTagSet("37", "abi3", "minix3_x64")
    assert tag_set.supported_abis() == ["abi3", "none"]
    tag_set = pep425.CPythonTagSet("37", platform="minix3_x64")
    assert tag_set.supported_abis() == ["none"]


def test_cpython_platform_possibilities():
    tag_set = pep425.CPythonTagSet("37", "abi3", "minix3_x64")
    assert tag_set.supported_platforms() == ["minix3_x64", "any"]
    tag_set = pep425.CPythonTagSet("37", "abi3")
    assert tag_set.supported_platforms() == ["any"]
