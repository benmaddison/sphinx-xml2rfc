# Copyright (c) 2021 Ben Maddison. All rights reserved.
#
# The contents of this file are licensed under the MIT License
# (the "License"); you may not use this file except in compliance with the
# License.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""sphinx_xml2rfc documentation config."""

from __future__ import annotations

import datetime
import importlib.metadata
import os
import sys

import sphinx_readable_theme

import sphinx_xml2rfc

_dist = importlib.metadata.distribution(sphinx_xml2rfc.__name__)
_buildtime = datetime.datetime.utcnow()

# -- Project Information

project = _dist.metadata["name"]
author = _dist.metadata["author"]

_from_year = 2021
_to_year = _buildtime.year
if _from_year < _to_year:
    _year_range = f"{_from_year}-{_to_year}"
else:
    _year_range = f"{_from_year}"
copyright = f"{_year_range}, {author}"

release = _dist.version
version = ".".join(release.split(".")[:2])

# -- General configuration

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             "_extensions")))
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "myst_parser",
]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
exclude_patterns = []

# -- HTML output

html_theme = "readable"
html_theme_path = [sphinx_readable_theme.get_html_theme_path()]

# -- Autodoc configuration

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_typehints_description_target = "all"


# -- Intersphinx configuration

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Markdown processing

myst_enable_extensions = [
    "colon_fence",
]
