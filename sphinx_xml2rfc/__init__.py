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
"""xml2rfc document generation extension."""

from __future__ import annotations

import typing

import sphinx

from .autogen import autogen_run
from .domain import Xml2rfcDomain

logger = sphinx.util.logging.getLogger(__name__)


def setup(app: sphinx.application.Sphinx) -> typing.Dict[str, typing.Any]:
    """Sphinx extension for xml2rfc rendering."""
    app.add_config_value("xml2rfc_drafts", [], "env")
    app.add_config_value("xml2rfc_sources", [], "env")
    app.add_config_value("xml2rfc_remotes", ["origin"], "env")
    app.add_config_value("xml2rfc_autogen_docs", True, "env")
    app.add_config_value("xml2rfc_autogen_branch_re", r"^main|master$", "env")
    app.add_config_value("xml2rfc_autogen_tag_re", r"^.+$", "env")
    app.add_config_value("xml2rfc_output", "_xml2rfc", "env")

    app.add_domain(Xml2rfcDomain)

    app.connect("builder-inited", autogen_run)

    return {"version": "0.0.1",
            "parallel_read_safe": True,
            "parallel_write_safe": True}
