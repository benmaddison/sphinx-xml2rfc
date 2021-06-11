# sphinx-xml2rfc

A `sphinx` extension providing features to document work-in-progress
Internet-Drafts using `git` history.

![PyPI](https://img.shields.io/pypi/v/sphinx-xml2rfc)
[![CI/CD](https://github.com/benmaddison/sphinx-xml2rfc/actions/workflows/cicd.yml/badge.svg)](https://github.com/benmaddison/sphinx-xml2rfc/actions/workflows/cicd.yml)
[![codecov](https://codecov.io/gh/benmaddison/sphinx-xml2rfc/branch/master/graph/badge.svg?token=YclUBHw70S)](https://codecov.io/gh/benmaddison/sphinx-xml2rfc)
[![Updates](https://pyup.io/repos/github/benmaddison/sphinx-xml2rfc/shield.svg)](https://pyup.io/repos/github/benmaddison/sphinx-xml2rfc/)

## Overview

The extension contains two primary components:

### Versioned document generation

Hooks `sphinx-build` initialisation, and searches the local `git` repository
for `refs`, and uses `xml2rfc` to build each version of the named drafts.

These are written to the `sphinx` source directory tree for use during the
build phase.

### `sphinx` language domain

The `xml2rfc` domain provides directives for rendering Internet-Draft texts
and for displaying changes between versions.

Documentation sources containing the appropriate directives can optionally be
auto-generated, after the fashion of `sphinx-apidoc`

## Installation

``` sh
python -m pip install sphinx-xml2rfc
```

## Usage

To use, add `sphinx_xml2rfc` to `extensions` in `conf.py`:

``` python
extensions = [
    ...,
    sphinx_xml2rfc,
    ...
]
```

The following configuration options are available:

-   `xml2rfc_drafts`

    Iterable of draft names for which to auto-generate text versions from xml
    sources using `xml2rfc`.

    Each name should match the name of the XML source file (without the `.xml`
    extension) in the root of the repository tree.

    default: `[]`

-   `xml2rfc_sources`

    Iterable of file names required by `xml2rfc` to process the documents in
    `xml2rfc_drafts`.

    default: `[]`

-   `xml2rfc_remotes`

    Iterable of git remote names to consider when searching for branch `refs`.

    Local `heads` will be considered first, after which each remote will be
    searched in order. Only the first branch `ref` with a given name will be
    used.

    default: `["origin"]`

-   `xml2rfc_autogen_docs`

    Enable the automatic generation of `sphinx` source documents.

    default: `True`

-   `xml2rfc_autogen_branch_re`

    Regex pattern for selection of branch names to generate document versions
    for.

    default: `r"^main|master$"`

-   `xml2rfc_autogen_tag_re`

    Regex pattern for selection of tag names to generate document versions for.

    default: `r"^.+$"`

-   `xml2rfc_output`

    Directory name in which to output files. Relative to `sphinx` `confdir`.

    default: `"_xml2rfc"`
