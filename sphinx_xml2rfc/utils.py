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
"""sphinx-xml2rfc utils module."""

from __future__ import annotations

import os
import typing

import sphinx

if typing.TYPE_CHECKING:
    import sphinx.application

logger = sphinx.util.logging.getLogger(__name__)


def get_base_dir(app: sphinx.application.Sphinx) -> str:
    """Get the absolute path to the base output directory."""
    return os.path.join(typing.cast(str, app.confdir),
                        app.config.xml2rfc_output)
