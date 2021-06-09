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
"""sphinx_xml2rfc test configuration."""

from __future__ import annotations

import datetime
import os
from unittest.mock import NonCallableMagicMock, PropertyMock, patch

import git

import pytest

from sphinx.testing.path import path

AUTOGEN_TEST_DRAFT = "test-draft"

pytest_plugins = 'sphinx.testing.fixtures'
collect_ignore = ["docs"]


@pytest.fixture(scope="session")
def rootdir():
    """Set the root directory of test sources."""
    return path(__file__).parent.abspath() / "roots"


@pytest.fixture(scope="session")
def test_draft_name():
    """Provide test draft name."""
    return "test-draft"


@pytest.fixture
def patched_app(test_draft_name, test_params, app_params,
                make_app, shared_result):
    """Provide a sphinx application with `git` patched."""

    def blob_stream_data(fd):
        """Write bytes from dummy draft."""
        with open(os.path.join(os.path.dirname(__file__),
                  f"{test_draft_name}.xml")) as f:
            template = f.read()
        text = template.format(version_path=fd.name)
        fd.write(text.encode())

    with patch("git.Repo", autospec=True) as MockRepo:  # noqa: N806
        mock_repo = MockRepo.return_value

        mock_blob = NonCallableMagicMock(spec=git.Blob)
        mock_blob.name = "test-draft.xml"
        mock_blob.stream_data.side_effect = blob_stream_data

        ref_specs = {"branches": {"name": "main",
                                  "path": "refs/heads/main",
                                  "repo": mock_repo},
                     "tags": {"name": "v0",
                              "path": "refs/tags/v0",
                              "repo": mock_repo}}
        mock_refs = list()
        for prop, ref_attrs in ref_specs.items():
            mock_ref = NonCallableMagicMock(spec=git.Reference)
            mock_ref.configure_mock(**ref_attrs)
            mock_ref.commit.committed_datetime = datetime.datetime.utcnow()
            type(mock_ref.commit.tree).blobs = PropertyMock(return_value=[mock_blob])  # noqa: E501
            setattr(type(mock_repo), prop, PropertyMock(return_value=[mock_ref]))  # noqa: E501
            mock_refs.append(mock_ref)

        args, kwargs = app_params
        app_ = make_app(*args, **kwargs)
        yield (app_, MockRepo, mock_refs, mock_blob)

        print('# testroot:', kwargs.get('testroot', 'root'))
        print('# builder:', app_.builder.name)
        print('# srcdir:', app_.srcdir)
        print('# outdir:', app_.outdir)
        print('# status:', '\n' + app_._status.getvalue())
        print('# warning:', '\n' + app_._warning.getvalue())

        if test_params['shared_result']:
            shared_result.store(test_params['shared_result'], app_)
