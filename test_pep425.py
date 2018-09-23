import pep425


def test_Tag_lowercasing():
    tag = pep425.Tag("PY3", "None", "ANY")
    assert tag.interpreter == "py3"
    assert tag.abi == "none"
    assert tag.platform == "any"


def test_Tag_equality():
    args = "py3", "none", "any"
    assert pep425.Tag(*args) == pep425.Tag(*args)


def test_Tag_hashing():
    tag = pep425.Tag("py3", "none", "any")
    tags = {tag}  # Should not raise TypeError.


def test_Tag_str():
    tag = pep425.Tag("py3", "none", "any")
    assert str(tag) == "py3-none-any"


def test_Tag_attribute_access():
    tag = pep425.Tag("py3", "none", "any")
    assert tag.interpreter == "py3"
    assert tag.abi == "none"
    assert tag.platform == "any"
