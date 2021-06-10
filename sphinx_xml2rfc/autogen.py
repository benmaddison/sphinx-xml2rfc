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
"""sphinx-xml2rfc autogen module."""

from __future__ import annotations

import datetime
import itertools
import os
import re
import subprocess  # noqa: S404
import tempfile
import typing

import git

import sphinx

from .utils import get_base_dir

if typing.TYPE_CHECKING:
    import sphinx.application

logger = sphinx.util.logging.getLogger(__name__)

Refs = typing.Dict[str, typing.Dict[str, git.refs.reference.Reference]]


def autogen_run(app: sphinx.application.Sphinx) -> None:
    """Generate text output from XML sources at every git ref."""
    if app.config.xml2rfc_drafts:
        refs = autogen_select_refs(app)
        autogen = Autogen(app, refs)
        if app.config.xml2rfc_autogen_docs:
            autogen.gen_docs()
    return


def autogen_select_refs(app: sphinx.application.Sphinx) -> Refs:
    """Select git refs to include."""
    branch_re = re.compile(app.config.xml2rfc_autogen_branch_re)
    tag_re = re.compile(app.config.xml2rfc_autogen_tag_re)
    repo = git.Repo(path=os.path.dirname(__file__),
                    search_parent_directories=True)
    refs = {"branches": {b.name: b for b in repo.branches
                         if branch_re.match(b.name)},
            "tags": {t.name: t for t in repo.tags
                     if tag_re.match(t.name)}}
    for remote in app.config.xml2rfc_remotes:
        for ref in repo.remotes[remote].refs:
            if (branch_re.match(ref.remote_head)
                    and ref.remote_head not in refs["branches"]
                    and ref.is_detached):
                refs["branches"][ref.remote_head] = ref
    logger.debug(f"{refs=}")
    return refs


class AutoVersion(typing.NamedTuple):
    """Auto generated draft version."""

    draft: str
    ref_type: str
    ref_name: str
    ref: git.refs.reference.Reference

    @property
    def ts(self) -> datetime.datetime:
        """Get the committed date-time of the commit at `self.ref`."""
        return typing.cast(datetime.datetime,
                           self.ref.commit.committed_datetime)


class Autogen(object):
    """Document auto-generator."""

    _Items = typing.ItemsView[str, typing.Dict[str, typing.List[AutoVersion]]]

    def __init__(self, app: sphinx.application.Sphinx, refs: Refs) -> None:
        """Auto generate draft versions."""
        self.app = app
        self.base_dir = get_base_dir(self.app)
        proc = subprocess.run(("xml2rfc", "--version"),  # noqa: S603
                              capture_output=True, check=True)
        xml2rfc_version = proc.stdout.decode().strip()
        logger.info(f"sphinx-xml2rfc: using {xml2rfc_version}")

        file_names = [f"{draft}.xml" for draft in app.config.xml2rfc_drafts]
        file_names += app.config.xml2rfc_sources

        self.versions = list()
        for ref_type, _refs in refs.items():
            for ref_name, ref in _refs.items():
                output_dir = os.path.join(self.base_dir, *ref.path.split("/"))
                os.makedirs(output_dir, exist_ok=True)
                logger.debug(f"{output_dir=}")
                with tempfile.TemporaryDirectory() as tmpdir:
                    logger.debug(f"{ref_name=}, {ref.path=}")
                    for blob in ref.commit.tree.blobs:
                        if blob.name not in file_names:
                            continue
                        logger.debug(f"{blob.name=}")
                        logger.debug(f"{blob.hexsha=}")
                        with open(os.path.join(tmpdir, blob.name), "wb") as f:
                            blob.stream_data(f)
                    for draft in app.config.xml2rfc_drafts:
                        logger.info(f"generating output for {draft} "
                                    f"at {ref.path}")
                        src_path = os.path.join(tmpdir, f"{draft}.xml")
                        version = AutoVersion(draft, ref_type, ref_name, ref)
                        date = version.ts.strftime("%Y-%m-%d")
                        cmd = ("xml2rfc", src_path,
                               "--date", date,
                               "--no-pagination",
                               "--text",
                               "--path", output_dir)
                        logger.debug(f"{cmd=}")
                        try:
                            proc = subprocess.run(cmd, check=True,  # noqa: E501,S603
                                                  capture_output=True)
                        except subprocess.CalledProcessError as e:
                            logger.warning(e.stderr.decode())
                            continue
                        logger.debug(proc.stderr.decode())
                        self.versions.append(version)

    def version_items(self) -> _Items:
        """Get an `ItemsView` of a `dict` of generated versions."""
        d = {draft: {ref_type: [version for version in it]
                     for ref_type, it
                     in itertools.groupby(it, lambda v: v.ref_type)}
             for draft, it
             in itertools.groupby(sorted(self.versions), lambda v: v.draft)}
        return d.items()

    def sorted_versions(self, draft: str) -> typing.Iterator[AutoVersion]:
        """Iterate over versions of `draft` in reserve chronological order."""
        for version in sorted(self.versions, key=lambda v: v.ts, reverse=True):
            if version.draft == draft:
                yield version

    def prior_versions(self,
                       version: AutoVersion) -> typing.Iterator[AutoVersion]:
        """Iterate over prior versions of `version`."""
        for prior in self.sorted_versions(version.draft):
            if prior.ts < version.ts:
                yield prior

    def gen_docs(self) -> None:
        """Generate markdown sources for building by sphinx."""
        if not self.versions:
            return
        with open(os.path.join(self.base_dir, "toc.md"), "w",
                  encoding="utf-8") as toc_fd:
            toc_fd.write("# Internet Drafts\n\n"
                         ":::{toctree}\n"
                         ":maxdepth: 3\n\n")
            for draft, ref_types in self.version_items():
                draft_toc = f"toc-{draft}"
                toc_fd.write(f"{draft_toc}\n")
                with open(os.path.join(self.base_dir, f"{draft_toc}.md"),
                          "w", encoding="utf-8") as draft_toc_fd:
                    draft_toc_fd.write(f"# `{draft}`\n\n"
                                       f":::{{toctree}}\n\n")
                    for ref_type, versions in ref_types.items():
                        ref_type_toc = f"{draft_toc}-{ref_type}"
                        draft_toc_fd.write(f"{ref_type_toc}\n")
                        with open(os.path.join(self.base_dir, f"{ref_type_toc}.md"),  # noqa: E501
                                  "w", encoding="utf-8") as ref_type_toc_fd:
                            ref_type_toc_fd.write(f"# {ref_type}\n\n"
                                                  f":::{{toctree}}\n\n")
                            for version in versions:
                                draft_doc = os.path.join(
                                    *version.ref.path.split("/"),
                                    draft,
                                )
                                ref_type_toc_fd.write(f"{draft_doc}\n")
                                with open(os.path.join(self.base_dir, f"{draft_doc}.md"),  # noqa: E501
                                          "w", encoding="utf-8") as draft_fd:
                                    draft_fd.write(f"# {version.ref_type}: {version.ref_name}\n\n"  # noqa: E501
                                                   f":::{{xml2rfc:version}} {draft}\n"  # noqa: E501
                                                   f":ref_type: {version.ref_type}\n"  # noqa: E501
                                                   f":ref_name: {version.ref_name}\n"  # noqa: E501
                                                   f":ref_path: {version.ref.path}\n"  # noqa: E501
                                                   f":::\n")
                            ref_type_toc_fd.write(":::\n")
                    changes_toc = f"{draft_toc}-diffs"
                    draft_toc_fd.write(f"{changes_toc}\n")
                    with open(os.path.join(self.base_dir, f"{changes_toc}.md"),
                              "w", encoding="utf-8") as changes_toc_fd:
                        changes_toc_fd.write("# changes\n\n"
                                             ":::{toctree}\n\n")
                        for to_ver in self.sorted_versions(draft):
                            for from_ver in self.prior_versions(to_ver):
                                changes_doc = os.path.join(
                                    *to_ver.ref.path.split("/"),
                                    f"{draft}-diff-from-"
                                    f"{from_ver.ref_type}.{from_ver.ref_name}",
                                )
                                changes_toc_fd.write(f"{changes_doc}\n")
                                with open(os.path.join(self.base_dir, f"{changes_doc}.md"),  # noqa: E501
                                          "w", encoding="utf-8") as changes_doc_fd:  # noqa: E501
                                    changes_doc_fd.write(f"# {from_ver.ref.path} ⟼ {to_ver.ref.path}\n\n"  # noqa: E501
                                                         f":::{{xml2rfc:diff}} {draft}\n"  # noqa: E501
                                                         f":from: {from_ver.ref.path}\n"  # noqa: E501
                                                         f":to: {to_ver.ref.path}\n"  # noqa: E501
                                                         f":::\n")
                        changes_toc_fd.write(":::\n")
                    draft_toc_fd.write(":::\n")
            toc_fd.write(":::\n")
        return
