from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from tools import content_inventory, migrate_frontmatter, validate_frontmatter
from tools.iot_domain import (
    LAYERS,
    LAYER_ID_BY_SLUG,
    ContentError,
    canonical_body_bytes,
    content_title,
    iter_content_documents,
    layer_by_id,
    layer_by_name,
    layer_by_plan_file,
    layer_by_slug,
    parse_document,
)
from tools.iot_domain.content import first_body_h1, parse_frontmatter_bytes


EXPECTED_LAYERS = (
    (1, "foundation", "感知与硬件", "layer1-foundation.json"),
    (2, "connectivity", "无线接入", "layer2-connectivity.json"),
    (3, "network", "网络协议", "layer3-network.json"),
    (4, "computing", "计算平台", "layer4-computing.json"),
    (5, "intelligence", "边缘智能", "layer5-intelligence.json"),
    (6, "security", "安全与隐私", "layer6-security.json"),
    (7, "applications", "综合应用", "layer7-applications.json"),
    (8, "frontier", "前沿方向", "layer8-frontier.json"),
)


class LayerRegistryTests(unittest.TestCase):
    def test_registry_is_complete_immutable_and_bidirectional(self) -> None:
        self.assertEqual(EXPECTED_LAYERS, tuple(tuple(layer) for layer in LAYERS))
        self.assertEqual(8, len({layer.id for layer in LAYERS}))
        self.assertEqual(8, len({layer.slug for layer in LAYERS}))
        for layer in LAYERS:
            self.assertIs(layer, layer_by_id(layer.id))
            self.assertIs(layer, layer_by_slug(layer.slug))
            self.assertIs(layer, layer_by_name(layer.name))
            self.assertIs(layer, layer_by_plan_file(layer.plan_file))
            layer_id, slug, name, plan_file = layer
            self.assertEqual((layer.id, layer.slug, layer.name, layer.plan_file), (layer_id, slug, name, plan_file))
        with self.assertRaises(TypeError):
            LAYERS[0] = LAYERS[1]  # type: ignore[index]

    def test_legacy_tools_reference_domain_registry_views(self) -> None:
        self.assertIs(content_inventory.LAYERS, LAYERS)
        self.assertIs(validate_frontmatter.LAYER_BY_SLUG, LAYER_ID_BY_SLUG)


class CanonicalBodyTests(unittest.TestCase):
    def test_only_first_lf_frontmatter_block_is_removed(self) -> None:
        raw = b"---\ntitle: Demo\n---\n# Demo\n\n---\nbody\n"
        self.assertEqual(b"# Demo\n\n---\nbody\n", canonical_body_bytes(raw))

    def test_crlf_and_trailing_newline_are_not_normalized(self) -> None:
        crlf = b"---\r\ntitle: Demo\r\n---\r\n# Demo\r\n"
        lf = b"---\ntitle: Demo\n---\n# Demo\n"
        no_trailing_newline = b"---\ntitle: Demo\n---\n# Demo"
        self.assertEqual(b"# Demo\r\n", canonical_body_bytes(crlf))
        self.assertNotEqual(canonical_body_bytes(crlf), canonical_body_bytes(lf))
        self.assertNotEqual(canonical_body_bytes(lf), canonical_body_bytes(no_trailing_newline))

    def test_frontmatter_changes_do_not_change_body_hash(self) -> None:
        first = b"---\ntitle: Demo\ntags: []\n---\n# Demo\nbody\n"
        second = b"---\ntitle: Demo\ntags: [iot]\n---\n# Demo\nbody\n"
        first_body = canonical_body_bytes(first)
        second_body = canonical_body_bytes(second)
        self.assertEqual(first_body, second_body)
        self.assertEqual(hashlib.sha256(first_body).digest(), hashlib.sha256(second_body).digest())

    def test_indented_yaml_separator_is_not_a_closing_delimiter(self) -> None:
        raw = (
            b"---\n"
            b"id: demo\n"
            b"title: |\n"
            b"  ---\n"
            b"layer: 3\n"
            b"---\n"
            b"# ---\nbody\n"
        )
        self.assertEqual(b"# ---\nbody\n", canonical_body_bytes(raw))

    def test_h1_scanner_matches_python_markdown_atx_and_fence_rules(self) -> None:
        self.assertEqual("Demo", first_body_h1(b"# Demo #\n"))
        self.assertEqual("Demo", first_body_h1(b"    ```\n# Demo\n"))
        self.assertEqual("Demo", first_body_h1(b"   ```\n# Demo\n```\n"))
        self.assertIsNone(first_body_h1(b"   # Indented paragraph\n"))

    def test_html_comment_marker_inside_inline_code_remains_visible(self) -> None:
        self.assertEqual(
            "Literal `<!--` marker",
            first_body_h1(b"# Literal `<!--` marker\n"),
        )

    def test_html_comment_inside_fence_does_not_hide_later_h1(self) -> None:
        body = b"```html\n<!--\n```\n# Demo\n"
        self.assertEqual("Demo", first_body_h1(body))

    def test_duplicate_keys_and_recursive_aliases_are_structured_errors(self) -> None:
        duplicate = b"---\ntitle: First\ntitle: Second\n---\n# Second\n"
        recursive = b"---\ntitle: Demo\nvalue: &value [*value]\n---\n# Demo\n"
        for raw in (duplicate, recursive):
            with self.subTest(raw=raw):
                with self.assertRaises(ContentError) as caught:
                    parse_frontmatter_bytes(raw, path="demo.md")
                self.assertEqual(
                    "INVALID_FRONTMATTER_YAML",
                    caught.exception.issue.code,
                )

    def test_body_changes_change_hash_and_plain_body_is_preserved(self) -> None:
        plain = b"# Demo\nbody\n"
        changed = b"# Demo\nbody changed\n"
        self.assertEqual(plain, canonical_body_bytes(plain))
        self.assertNotEqual(hashlib.sha256(plain).digest(), hashlib.sha256(changed).digest())

    def test_unclosed_frontmatter_is_a_structured_error(self) -> None:
        with self.assertRaises(ContentError) as caught:
            canonical_body_bytes(b"---\ntitle: Demo\n# Demo\n")
        self.assertEqual("MISSING_FRONTMATTER_CLOSE", caught.exception.issue.code)


class ContentParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _paper_path(self, content_id: str = "demo", slug: str = "network") -> Path:
        path = self.root / "docs" / slug / "papers" / f"{content_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _raw_document(
        *,
        content_id: str = "demo",
        layer: int = 3,
        title: str = "Demo",
        body: bytes = b"# Demo\nbody\n",
    ) -> bytes:
        prefix = (
            "---\n"
            "schema_version: '1.0'\n"
            f"id: {content_id}\n"
            f"title: {title}\n"
            f"layer: {layer}\n"
            "---\n"
        ).encode("utf-8")
        return prefix + body

    def test_document_exposes_canonical_identity_title_and_body_hash(self) -> None:
        path = self._paper_path()
        raw = self._raw_document()
        path.write_bytes(raw)
        document = parse_document(path, repo_root=self.root)
        self.assertEqual("docs/network/papers/demo.md", document.repo_relative_path)
        self.assertEqual("network", document.layer.slug)
        self.assertEqual("demo", document.content_id)
        self.assertEqual("Demo", document.frontmatter_title)
        self.assertEqual("Demo", document.body_h1)
        self.assertEqual(b"# Demo\nbody\n", document.body_bytes)
        self.assertEqual(hashlib.sha256(document.body_bytes).hexdigest(), document.body_sha256)
        self.assertEqual("Demo", content_title(document))
        self.assertTrue(document.raw_frontmatter_bytes.startswith(b"---\n"))

    def test_title_h1_mismatch_is_structured_and_read_only(self) -> None:
        path = self._paper_path("mismatch")
        before = self._raw_document(
            content_id="mismatch",
            title="Frontmatter title",
            body=b"# Body title\nbody\n",
        )
        path.write_bytes(before)
        with self.assertRaises(ContentError) as caught:
            parse_document(path, repo_root=self.root)
        issue = caught.exception.issue
        self.assertEqual("TITLE_H1_MISMATCH", issue.code)
        self.assertEqual("docs/network/papers/mismatch.md", issue.path)
        self.assertEqual("title", issue.location)
        self.assertIn("title/H1 mismatch", issue.message)
        self.assertEqual(before, path.read_bytes())

    def test_fenced_and_commented_h1_do_not_satisfy_title_invariant(self) -> None:
        path = self._paper_path("hidden")
        path.write_bytes(
            self._raw_document(
                content_id="hidden",
                body=(
                    b"```markdown\n"
                    b"```not-a-closing-fence\n"
                    b"# Demo\n"
                    b"```\n"
                    b"<!--\n"
                    b"# Demo\n"
                    b"-->\n"
                ),
            )
        )
        with self.assertRaises(ContentError) as caught:
            parse_document(path, repo_root=self.root)
        self.assertEqual("MISSING_BODY_H1", caught.exception.issue.code)

    def test_id_and_layer_mismatches_have_stable_codes(self) -> None:
        wrong_id = self._paper_path("path-id")
        wrong_id.write_bytes(self._raw_document(content_id="frontmatter-id"))
        with self.assertRaises(ContentError) as caught_id:
            parse_document(wrong_id, repo_root=self.root)
        self.assertEqual("CONTENT_ID_MISMATCH", caught_id.exception.issue.code)

        wrong_layer = self._paper_path("wrong-layer")
        wrong_layer.write_bytes(self._raw_document(content_id="wrong-layer", layer=2))
        with self.assertRaises(ContentError) as caught_layer:
            parse_document(wrong_layer, repo_root=self.root)
        self.assertEqual("CONTENT_LAYER_MISMATCH", caught_layer.exception.issue.code)

    def test_unknown_layer_and_invalid_utf8_have_stable_codes(self) -> None:
        unknown = self._paper_path("demo", slug="unknown")
        unknown.write_bytes(self._raw_document())
        with self.assertRaises(ContentError) as caught_layer:
            parse_document(unknown, repo_root=self.root)
        self.assertEqual("UNKNOWN_LAYER", caught_layer.exception.issue.code)

        invalid_utf8 = self._paper_path("invalid-utf8")
        invalid_utf8.write_bytes(
            self._raw_document(content_id="invalid-utf8", body=b"# Demo\n\xff\n")
        )
        with self.assertRaises(ContentError) as caught_utf8:
            parse_document(invalid_utf8, repo_root=self.root)
        self.assertEqual("INVALID_UTF8", caught_utf8.exception.issue.code)

    def test_outside_and_symlink_alias_paths_are_rejected_before_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as outside_directory:
            outside = Path(outside_directory) / "invalid.md"
            outside.write_bytes(b"\xff")
            with self.assertRaises(ContentError) as caught_outside:
                parse_document(outside, repo_root=self.root)
            self.assertEqual("INVALID_CONTENT_PATH", caught_outside.exception.issue.code)

            outside_loop = Path(outside_directory) / "loop.md"
            outside_loop.symlink_to(outside_loop.name)
            with self.assertRaises(ContentError) as caught_outside_loop:
                parse_document(outside_loop, repo_root=self.root)
            self.assertEqual(
                "INVALID_CONTENT_PATH",
                caught_outside_loop.exception.issue.code,
            )

        canonical = self._paper_path("canonical")
        canonical.write_bytes(self._raw_document(content_id="canonical"))
        alias = self._paper_path("alias")
        alias.symlink_to(canonical)
        with self.assertRaises(ContentError) as caught_alias:
            parse_document(alias, repo_root=self.root)
        self.assertEqual("INVALID_CONTENT_PATH", caught_alias.exception.issue.code)

        loop = self._paper_path("loop")
        loop.symlink_to(loop.name)
        with self.assertRaises(ContentError) as caught_loop:
            parse_document(loop, repo_root=self.root)
        self.assertEqual("INVALID_CONTENT_PATH", caught_loop.exception.issue.code)

    def test_dot_segments_normalize_to_one_repository_identity(self) -> None:
        canonical = self._paper_path("normalized")
        canonical.write_bytes(self._raw_document(content_id="normalized"))
        dotted = Path("docs/network/papers/../papers/normalized.md")
        document = parse_document(dotted, repo_root=self.root)
        self.assertEqual("docs/network/papers/normalized.md", document.repo_relative_path)
        self.assertEqual(canonical, document.path)

    def test_explicit_cli_paths_reject_escape_symlink_before_reading(self) -> None:
        with tempfile.TemporaryDirectory() as outside_directory:
            outside = Path(outside_directory) / "invalid.md"
            outside.write_bytes(b"\xff")
            alias = self._paper_path("external-alias")
            alias.symlink_to(outside)

            for module, argv in (
                (validate_frontmatter, ["--path", "docs/network/papers/external-alias.md"]),
                (validate_frontmatter, ["--path", outside.as_posix()]),
                (
                    migrate_frontmatter,
                    ["--path", "docs/network/papers/external-alias.md", "--dry-run"],
                ),
                (migrate_frontmatter, ["--path", outside.as_posix(), "--dry-run"]),
            ):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with (
                    mock.patch.object(module, "ROOT", self.root),
                    redirect_stdout(stdout),
                    redirect_stderr(stderr),
                ):
                    result = module.main(argv)
                self.assertEqual(1, result)
                self.assertIn("content file", stderr.getvalue())
                self.assertNotIn("UTF-8", stderr.getvalue())


class RepositoryCorpusTests(unittest.TestCase):
    def test_repository_enumeration_and_body_manifest_are_stable(self) -> None:
        root = content_inventory.ROOT
        first = tuple(iter_content_documents(repo_root=root))
        second = tuple(iter_content_documents(repo_root=root))
        first_paths = [document.repo_relative_path for document in first]
        self.assertEqual(first_paths, [document.repo_relative_path for document in second])
        self.assertEqual(sorted(first_paths), first_paths)
        self.assertEqual(657, len(first))
        self.assertEqual(657, len({document.content_id for document in first}))

        manifest = hashlib.sha256()
        for document in first:
            self.assertEqual(document.path.stem, document.content_id)
            self.assertEqual(hashlib.sha256(document.body_bytes).hexdigest(), document.body_sha256)
            self.assertEqual(document.frontmatter_title, document.body_h1)
            manifest.update(document.repo_relative_path.encode("utf-8"))
            manifest.update(b"\0")
            manifest.update(document.body_sha256.encode("ascii"))
            manifest.update(b"\0")
        self.assertEqual(
            "c8a8e40993edc019104997117fc19ff8389207f71fe2a7416f56d04d7bad0823",
            manifest.hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
