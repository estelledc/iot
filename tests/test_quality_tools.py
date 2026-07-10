from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import (
    check_markdown_fences,
    check_markdown_links,
    check_release_metadata,
    content_inventory,
    validate_site,
)


class ContentInventoryTests(unittest.TestCase):
    def test_generated_inventory_is_current_and_deterministic(self) -> None:
        first = content_inventory.content_inventory()
        second = content_inventory.content_inventory()
        self.assertEqual(
            content_inventory._json_bytes(first),
            content_inventory._json_bytes(second),
        )
        self.assertEqual([], content_inventory.check_inventory(first))


class HomepageSourceTruthTests(unittest.TestCase):
    def test_editable_home_content_lives_in_markdown(self) -> None:
        root = content_inventory.ROOT
        template = (root / "overrides/home.html").read_text(encoding="utf-8")
        markdown = (root / "docs/index.md").read_text(encoding="utf-8")
        self.assertIn("{{ page.content }}", template)
        self.assertNotIn("物联网全栈技术学习站", template)
        self.assertIn("物联网全栈技术学习站", markdown)


class MarkdownQualityToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.old_link_root = check_markdown_links.ROOT
        self.old_docs_root = check_markdown_links.DOCS_ROOT
        self.old_fence_root = check_markdown_fences.ROOT
        check_markdown_links.ROOT = self.root
        check_markdown_links.DOCS_ROOT = self.root / "docs"
        check_markdown_fences.ROOT = self.root

    def tearDown(self) -> None:
        check_markdown_links.ROOT = self.old_link_root
        check_markdown_links.DOCS_ROOT = self.old_docs_root
        check_markdown_fences.ROOT = self.old_fence_root
        self.tempdir.cleanup()

    def test_missing_relative_link_fails(self) -> None:
        source = self.root / "docs" / "index.md"
        source.parent.mkdir(parents=True)
        source.write_text("[missing](missing.md)\n", encoding="utf-8")
        errors = check_markdown_links.check_file(source, check_anchors=True)
        self.assertEqual(1, len(errors))
        self.assertIn("missing link target", errors[0])

    def test_existing_link_and_anchor_pass(self) -> None:
        source = self.root / "docs" / "index.md"
        target = self.root / "docs" / "guide.md"
        source.parent.mkdir(parents=True)
        source.write_text("[guide](guide.md#开始)\n", encoding="utf-8")
        target.write_text("# 开始\n", encoding="utf-8")
        self.assertEqual([], check_markdown_links.check_file(source, check_anchors=True))

    def test_heading_swallowed_by_bare_fence_fails(self) -> None:
        source = self.root / "broken.md"
        source.write_text("```\nnot code\n## swallowed\n```\n", encoding="utf-8")
        errors = check_markdown_fences.check_file(source)
        self.assertTrue(any("swallowed" in error for error in errors))


class ReleaseMetadataTests(unittest.TestCase):
    def test_repository_release_metadata_is_consistent(self) -> None:
        self.assertEqual(
            [],
            check_release_metadata.validate(
                check_release_metadata.ROOT / "VERSION",
                check_release_metadata.ROOT / "CHANGELOG.md",
            ),
        )

    def test_mismatched_version_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            version = root / "VERSION"
            changelog = root / "CHANGELOG.md"
            version.write_text("0.2.0\n", encoding="utf-8")
            changelog.write_text(
                "## [0.1.0] - 2026-07-10\n"
                "IOT-T001\n"
                + "a" * 40
                + "\n"
                + "b" * 64
                + "\n",
                encoding="utf-8",
            )
            errors = check_release_metadata.validate(version, changelog)
            self.assertTrue(any("does not match" in error for error in errors))


class SiteValidationTests(unittest.TestCase):
    def test_duplicate_landmarks_and_unsafe_blank_link_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            page.write_text(
                "<main><h1>Home</h1></main><main></main>"
                "<footer></footer><footer></footer>"
                '<a href="https://example.com" target="_blank">x</a>',
                encoding="utf-8",
            )
            errors = validate_site.validate_page(
                page,
                single_main=True,
                single_footer=True,
                single_h1=True,
                external_link_rel=True,
            )
            self.assertEqual(3, len(errors))

    def test_expected_structure_text_and_link_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            page.write_text(
                "<main><h1>物联网全栈技术学习站</h1>"
                '<a href="foundation/">Layer 1</a></main>'
                "<footer></footer>",
                encoding="utf-8",
            )
            self.assertEqual(
                [],
                validate_site.validate_page(
                    page,
                    single_main=True,
                    single_footer=True,
                    single_h1=True,
                    expected_text=["物联网全栈技术学习站"],
                    expected_links=["foundation/"],
                ),
            )


if __name__ == "__main__":
    unittest.main()
