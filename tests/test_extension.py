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
"""sphinx_xml2rfc package tests."""

from __future__ import annotations

import pytest


class TestExtension:
    """Test cases for sphinx_xml2rfc."""

    @pytest.mark.sphinx("html", testroot="ext-xml2rfc", freshenv=True)
    def test_domain(self, app):
        """Test `xml2rfc` directives."""
        app.builder.build_all()
        content = (app.outdir / "index.html").read_text()
        # check tiitle
        assert "<h1>Test sphinx-xml2rfc" in content
        # check versions
        assert "Test I-D Foo" in content
        assert "Test I-D Bar" in content
        # check diff
        assert "-Test I-D Foo" in content
        assert "+Test I-D Bar" in content

    @pytest.mark.sphinx("html", testroot="ext-xml2rfc-autogen", freshenv=True)
    def test_autogen(self, test_draft_name, patched_app):  # noqa: R701
        """Test document auto-generation."""
        (app, mock_repo, mock_refs, mock_blob) = patched_app
        app.builder.build_all()
        assert mock_repo.called
        assert mock_blob.stream_data.call_count == len(mock_refs)
        outdir = app.confdir / "_xml2rfc"
        toc_root = (outdir / "toc.md").read_text()
        assert "Internet Drafts" in toc_root
        assert "toctree" in toc_root
        assert f"toc-{test_draft_name}" in toc_root
        toc_draft = (outdir / f"toc-{test_draft_name}.md").read_text()
        assert f"`{test_draft_name}`" in toc_draft
        assert "toctree" in toc_draft
        for ref_type in ("branches", "tags", "diffs"):
            assert f"toc-{test_draft_name}-{ref_type}" in toc_draft
            toc_ref_type = (outdir /
                            f"toc-{test_draft_name}-{ref_type}.md").read_text()
            assert "toctree" in toc_ref_type
