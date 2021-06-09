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
"""sphinx-xml2rfc domain module."""

from __future__ import annotations

import difflib
import itertools
import os
import typing

import docutils

import sphinx

from .utils import get_base_dir

if typing.TYPE_CHECKING:
    import sphinx.application
    import sphinx.directives
    import sphinx.domains

logger = sphinx.util.logging.getLogger(__name__)


class VersionDirective(sphinx.directives.ObjectDescription[str]):
    """RST xml2rfc:version directive."""

    has_content = False
    required_arguments = 1
    option_spec = {
        "ref_type": docutils.parsers.rst.directives.unchanged_required,
        "ref_name": docutils.parsers.rst.directives.unchanged_required,
        "ref_path": docutils.parsers.rst.directives.unchanged_required,
    }

    def run(self) -> typing.List[docutils.nodes.Node]:
        """Save the version object for later processing."""
        self.version = Version(base_dir=get_base_dir(self.env.app),
                               draft=self.arguments[0].strip(),
                               ref_type=self.options.get("ref_type").strip(),
                               ref_name=self.options.get("ref_name").strip(),
                               ref_path=self.options.get("ref_path").strip())
        return super().run()

    def handle_signature(self, sig: str,
                         signode: sphinx.addnodes.desc_signature) -> str:
        """Handle the object signature."""
        signode += sphinx.addnodes.desc_name(text=sig)
        return sig

    def transform_content(self,
                          contentnode: sphinx.addnodes.desc_content) -> None:
        """Read the version source file and insert into the node."""
        src = self.version.read_src()
        code_block = docutils.nodes.literal_block(src, src)
        code_block["language"] = "text"
        contentnode += code_block

    def add_target_and_index(self, name: str, sig: str,
                             signode: sphinx.addnodes.desc_signature) -> None:
        """Add ourself to the domain."""
        signode["ids"].append(self.version.anchor)
        domain = self.env.get_domain("xml2rfc")
        typing.cast(Xml2rfcDomain, domain).add_version(self.version)


class Version(typing.NamedTuple):
    """Pickable object for storing version instance data."""

    base_dir: str
    draft: str
    ref_type: str
    ref_name: str
    ref_path: str

    @property
    def anchor(self) -> str:
        """Generate anchor for version node."""
        return f"xml2rfc-version-{self.draft}-{self.ref_type}-{self.ref_name}"

    def read_src(self) -> str:
        """Read draft text from file."""
        src_path = os.path.join(self.base_dir,
                                self.ref_path,
                                f"{self.draft}.txt")
        logger.info(f"reading internet draft content from {src_path}")
        with open(src_path) as fd:
            src = fd.read()
        return src


class VersionNotFound(Exception):
    """A version with a matching 'ref.path' could not be found."""

    pass


class DiffDirective(sphinx.directives.ObjectDescription[str]):
    """RST xml2rfc:diff directive."""

    has_content = False
    required_arguments = 1
    option_spec = {
        "from": docutils.parsers.rst.directives.unchanged_required,
        "to": docutils.parsers.rst.directives.unchanged_required,
    }

    def run(self) -> typing.List[docutils.nodes.Node]:
        """Save the version object for later processing."""
        self.diff = Diff(draft=self.arguments[0].strip(),
                         ref_from=self.options.get("from").strip(),
                         ref_to=self.options.get("to").strip())
        return super().run()

    def handle_signature(self, sig: str,
                         signode: sphinx.addnodes.desc_signature) -> str:
        """Handle the object signature."""
        signode += sphinx.addnodes.desc_name(text=sig)
        return sig

    def transform_content(self,
                          contentnode: sphinx.addnodes.desc_content) -> None:
        """Insert a placeholder node for later resolution."""
        target = f"{self.diff.ref_from}::{self.diff.ref_to}"
        refnode = sphinx.addnodes.pending_xref("", refdomain="xml2rfc",
                                               reftype="diff",
                                               reftarget=target)
        temp_msg = f"diff targets {target} not resolved"
        temp = docutils.nodes.literal(temp_msg, temp_msg)
        refnode += temp
        contentnode += refnode

    def add_target_and_index(self, name: str, sig: str,
                             signode: sphinx.addnodes.desc_signature) -> None:
        """Add ourself to the domain."""
        signode["ids"].append(self.diff.anchor)
        domain = self.env.get_domain("xml2rfc")
        typing.cast(Xml2rfcDomain, domain).add_diff(self.diff)


class Diff(typing.NamedTuple):
    """Pickable object for storing diff instance data."""

    draft: str
    ref_to: str
    ref_from: str

    @property
    def anchor(self) -> str:
        """Generate anchor for version node."""
        return f"xml2rfc-diff-{self.draft}-{self.ref_from}-{self.ref_to}"


class VersionsIndex(sphinx.domains.Index):
    """Sphinx object index for draft versions."""

    name = "version-index"
    localname = "Internet Draft Versions"
    shortname = "drafts"

    _Items = typing.Tuple[
        typing.List[
            typing.Tuple[
                str,
                typing.List[sphinx.domains.IndexEntry],
            ],
        ],
        bool,
    ]

    def generate(self,
                 docnames: typing.Optional[typing.Iterable[str]] = None) -> _Items:  # noqa: E501
        """Build the index from obects stored on the domain."""

        def by_ref_type(version: typing.Tuple[str, str, str,
                                              str, str, int]) -> str:
            return version[2]

        versions = self.domain.get_objects()
        index = [(group, [sphinx.domains.IndexEntry(name, 0, docname, anchor,
                                                    "", "", object_type)
                          for name, _, object_type, docname, anchor, _
                          in items])
                 for group, items in itertools.groupby(versions, by_ref_type)]
        logger.debug(f"{index=}")
        return index, True


class Xml2rfcDomain(sphinx.domains.Domain):
    """Sphinx language domain for draft versions and diffs."""

    name = "xml2rfc"
    roles = {"ref": sphinx.roles.XRefRole()}
    directives = {"version": VersionDirective,
                  "diff": DiffDirective}
    indices = [VersionsIndex]

    initial_data: typing.Dict[typing.Any, typing.Any] = {"versions": set(),
                                                         "diffs": set()}

    def get_objects(self) -> typing.Iterable[typing.Tuple[str, str, str,
                                                          str, str, int]]:
        """Iterate over objects to construct indices."""
        for version, docname in self.data["versions"]:
            name = display_name = f"{version.draft}@{version.ref_name}"
            object_type = self.object_type_name(version.ref_type)
            anchor = version.anchor
            priority = 1
            yield (name, display_name, object_type, docname, anchor, priority)

    @property
    def versions(self) -> typing.Iterator[Version]:
        """Iterate over versions."""
        for version, _ in self.data["versions"]:
            yield version

    def search_version(self, ref_path: str) -> Version:
        """Get a draft version by ref_path."""
        for version in self.versions:
            if version.ref_path == ref_path:
                return version
        raise VersionNotFound(ref_path)

    def resolve_xref(self, env: sphinx.environment.BuildEnvironment,
                     fromdocname: str, builder: sphinx.builders.Builder,
                     typ: str, target: str, node: sphinx.addnodes.pending_xref,
                     contnode: docutils.nodes.Element) -> typing.Optional[docutils.nodes.Element]:  # noqa: E501
        """Resolve pending xrefs."""
        if typ == "diff":
            return self.construct_diff(target)
        return None

    def construct_diff(self,
                       target: str) -> docutils.nodes.Element:
        """Populate diff node content."""
        (ref_from, ref_to) = target.split("::")
        from_version = self.search_version(ref_from)
        to_version = self.search_version(ref_to)
        diff_lines = difflib.unified_diff(from_version.read_src().split("\n"),
                                          to_version.read_src().split("\n"),
                                          fromfile=from_version.ref_path,
                                          tofile=to_version.ref_path)
        container = docutils.nodes.container()
        if diff_lines:
            desc_src = f"Changes {ref_from} ⟼ {ref_to}"
            desc = docutils.nodes.paragraph(desc_src, desc_src)
            diff_src = "\n".join(diff_lines)
            code_block = docutils.nodes.literal_block(diff_src, diff_src)
            code_block["language"] = "diff"
            container += [desc, code_block]
        else:
            desc_src = f"No changes {ref_from} ⟼ {ref_to}"
            desc = docutils.nodes.paragraph(desc_src, desc_src)
            container += desc
        return container

    @staticmethod
    def object_type_name(ref_type: str) -> str:
        """Construct object type names on the fly."""
        base_name = "Internet Draft Version"
        names = {"branches": "Branch",
                 "tags": "Tag"}
        try:
            return f"{base_name} ({names[ref_type]})"
        except KeyError:
            return base_name

    def add_version(self, version: Version) -> None:
        """Add a version to the domain."""
        self.data["versions"].add((version, self.env.docname))

    def add_diff(self, diff: Diff) -> None:
        """Add a diff to the domain."""
        self.data["diffs"].add((diff, self.env.docname))
