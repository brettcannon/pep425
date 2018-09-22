# pep425
A library for [PEP 425](https://www.python.org/dev/peps/pep-0425/) (Compatibility Tags for Built Distributions).

## Why?
I'm somewhat on a quest to
[fill in gaps in library support](https://groups.google.com/forum/#!topic/pypa-dev/91QdZ1vxLT8)
for the various steps of going from requesting a package to
installing its wheel. The goal is to make it such that pip is more of
a CLI on top of various packages (plus whatever
backwards-compatibility pip needs to provide).
